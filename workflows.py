import asyncio

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError


from shared import ApplyDecisionDetails

with workflow.unsafe.imports_passed_through():
	from activities import ProvisioningActivities
	from shared import TerraformRunDetails

# NOTE: for init, policy_check, plan and outputs, they shouldn't take longer
# than 300 seconds.
TERRAFORM_COMMON_TIMEOUT_SECS = 300


@workflow.defn
class ProvisionInfraWorkflow:

	def __init__(self) -> None:
		self._apply_approved = None
		self._tf_run_details = None
		self._reason = ""
		self._current_status = "uninitialized"
		self._progress = 0
		self._tf_plan_output = ""
		self._tf_outputs = {}

	def _custom_upsert(self, run_details: TerraformRunDetails, payload: dict):
		if run_details.include_custom_search_attrs:
			workflow.upsert_search_attributes(payload)

	@workflow.run
	async def run(self, terraform_run_details: TerraformRunDetails) -> dict:
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["uninitialized"]})
		self._tf_run_details = terraform_run_details

		# A simple retry policy to be used across some common, fast, TF
		tf_init_retry_policy = RetryPolicy(
			maximum_attempts=5,
			non_retryable_error_types=["TerraformInitError"],
		)

		self._custom_upsert(terraform_run_details, {"provisionStatus": ["initializing"]})

		self._progress = 10
		self._current_status = "initializing"
		await workflow.execute_activity_method(
			ProvisioningActivities.terraform_init,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=tf_init_retry_policy,
		)
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["initialized"]})
		self._progress = 20
		self._current_status = "initialized"

		tf_plan_retry_policy = RetryPolicy(
			initial_interval=timedelta(seconds=3),
			non_retryable_error_types=["TerraformMissingEnvVarsErrors"],
		)
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["planning"]})
		self._progress = 30
		self._current_status = "planning"
		self._tf_plan_output, tf_plan_output_json = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=tf_plan_retry_policy,
		)
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["planned"]})
		self._progress = 40
		self._current_status = "planned"

		terraform_run_details.plan = tf_plan_output_json

		policy_retry_policy = RetryPolicy(
			maximum_attempts=5,
			maximum_interval=timedelta(seconds=5),
			non_retryable_error_types=["PolicyCheckError"],
		)
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["policy_checking"]})
		self._progress = 50
		self._current_status = "checking policy"
		policy_not_failed = await workflow.execute_activity_method(
			ProvisioningActivities.policy_check,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=policy_retry_policy,
		)
		self._custom_upsert(terraform_run_details, {"provisionStatus": ["policy_checked"]})
		self._progress = 60
		self._current_status = "policy checked"

		hard_fail = terraform_run_details.hard_fail_policy and not policy_not_failed

		if not policy_not_failed and not hard_fail:
			self._custom_upsert(terraform_run_details, {"provisionStatus": ["awaiting_approval"]})
			self._current_status = "awaiting approval decision"
			workflow.logger.info("Workflow awaiting approval decision")
			await workflow.wait_condition(
				lambda: self._apply_approved is not None
			)

		# If the policy check passed or the apply was approved, apply the changes,
		# unless the policy check failed and the hard fail policy is set.
		show_output = {}
		tf_apply_destroy_retry_policy = RetryPolicy(
			initial_interval=timedelta(seconds=3),
			maximum_interval=timedelta(seconds=5),
			maximum_attempts=100,
			non_retryable_error_types=[],
		)

		if hard_fail:
			self._custom_upsert(terraform_run_details, {"provisionStatus": ["policy_hard_failed"]})
			self._progress = 100
			self._current_status = "policy_hard_failed"
			workflow.logger.info("Workflow apply hard failed policy check, no work to do.")
		elif policy_not_failed or self._apply_approved:
			self._custom_upsert(terraform_run_details, {"provisionStatus": ["applying"]})
			self._progress = 70
			self._current_status = "applying"
			apply_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_apply,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=terraform_run_details.apply_timeout_secs),
				heartbeat_timeout=timedelta(seconds=10),
				retry_policy=tf_apply_destroy_retry_policy,
			)
			self._custom_upsert(terraform_run_details, {"provisionStatus": ["applied"]})
			self._progress = 80
			self._current_status = "applied"

			workflow.logger.info(f"Workflow apply output {apply_output}")

			workflow.logger.info("Sleeping for 3 seconds to slow execution down")
			await asyncio.sleep(3)

			show_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_output,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
				retry_policy=tf_apply_destroy_retry_policy,
			)
		else:
			self._custom_upsert(terraform_run_details, {"provisionStatus": ["rejected"]})
			self._current_status = "rejected"
			workflow.logger.info("Workflow apply denied, no work to do.")

		if terraform_run_details.ephemeral:
			self._current_status = "waiting for destroy"
			workflow.logger.info(f"Sleeping for {terraform_run_details.ephemeral_ttl} seconds, then destroying the infrastructure")
			await asyncio.sleep(terraform_run_details.ephemeral_ttl)

			self._progress = 90
			self._current_status = "destroying"
			destroy_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_destroy,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
				retry_policy=tf_apply_destroy_retry_policy,
			)
			self._current_status = "destroyed"

			workflow.logger.info("Infrastructure destroyed")

			show_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_output,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
				retry_policy=tf_apply_destroy_retry_policy,
			)

		self._progress = 100

		return show_output

	@workflow.signal
	async def signal_apply_decision(self, decision: ApplyDecisionDetails) -> None:
		workflow.logger.info(f"Signal decision update received: {decision}")
		self._apply_approved = decision.is_approved

	@workflow.update
	async def update_apply_decision(self, decision: ApplyDecisionDetails) -> None:
		workflow.logger.info(f"Apply decision update received: {decision}")
		self._apply_approved = decision.is_approved
		self._reason = decision.reason

	@update_apply_decision.validator
	def validate_apply_decision(self, decision: ApplyDecisionDetails) -> None:
		if decision.reason == "":
			workflow.logger.info("Rejecting update apply decision, no reason provided.")
			raise ApplicationError("Update apply decision must include a reason.")

	@workflow.query
	def get_reason(self) -> str:
		workflow.logger.info("Reason query received.")
		return self._reason

	@workflow.query
	def get_current_status(self) -> str:
		workflow.logger.info("Status query received.")
		return self._current_status

	@workflow.query
	def get_plan(self) -> str:
		workflow.logger.info("Plan output query received.")
		return self._tf_plan_output

	@workflow.query
	def get_progress(self) -> int:
		workflow.logger.info("Progress query received.")
		return self._progress
