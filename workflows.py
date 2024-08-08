from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
# from temporalio.exceptions import ActivityError # TODO

from shared import TERRAFORM_COMMON_TIMEOUT_SECS

with workflow.unsafe.imports_passed_through():
	from activities import ProvisioningActivities
	from shared import TerraformRunDetails


@workflow.defn
class ProvisionInfraWorkflow:

	def __init__(self) -> None:
		self._apply_approved = None
		self._signal_reason = ""
		self._current_state = "uninitialized"
		self._tf_run_details = None

	@workflow.run
	async def run(self, terraform_run_details: TerraformRunDetails) -> str:
		self._tf_run_details = terraform_run_details

		# A simple retry policy to be used across some common, fast, TF
		tf_fast_op_retry_policy = RetryPolicy(
			maximum_attempts=5,
			non_retryable_error_types=["TerraformInitError"],
		)

		workflow.upsert_search_attributes({"provisionStatus": ["initializing"]})
		self._current_state = "initializing"
		await workflow.execute_activity_method(
			ProvisioningActivities.terraform_init,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=tf_fast_op_retry_policy,
		)
		workflow.upsert_search_attributes({"provisionStatus": ["initialized"]})
		self._current_state = "initialized"

		workflow.upsert_search_attributes({"provisionStatus": ["planning"]})
		self._current_state = "planning..."
		plan_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=tf_fast_op_retry_policy,
		)
		workflow.upsert_search_attributes({"provisionStatus": ["planned"]})
		self._current_state = "planned"

		terraform_run_details.plan = plan_output

		policy_retry_policy = RetryPolicy(
			maximum_attempts=5,
			maximum_interval=timedelta(seconds=5),
			non_retryable_error_types=["PolicyCheckError"],
		)
		workflow.upsert_search_attributes({"provisionStatus": ["policy_checking"]})
		self._current_state = "checking policy"
		policy_check_output = await workflow.execute_activity_method(
			ProvisioningActivities.policy_check,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
			retry_policy=policy_retry_policy,
		)
		workflow.upsert_search_attributes({"provisionStatus": ["policy_checked"]})
		self._current_state = "policy checked"

		if not policy_check_output:
			workflow.upsert_search_attributes({"provisionStatus": ["awaiting_approval"]})
			self._current_state = "awaiting approval decision..."
			workflow.logger.info("Workflow awaiting approval decision")
			await workflow.wait_condition(
				lambda: self._apply_approved is not None
			)

		# If the policy check passed or the apply was approved, apply the changes
		show_output = ""
		if policy_check_output or self._apply_approved:
			workflow.upsert_search_attributes({"provisionStatus": ["applying"]})
			self._current_state = "applying"
			tf_apply_retry_policy = RetryPolicy(
				maximum_attempts=5,
				maximum_interval=timedelta(seconds=5),
				non_retryable_error_types=[],
			)
			apply_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_apply,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=terraform_run_details.apply_timeout_secs),
				heartbeat_timeout=timedelta(seconds=3),
				retry_policy=tf_apply_retry_policy,
			)
			workflow.upsert_search_attributes({"provisionStatus": ["applied"]})
			self._current_state = "applied"

			workflow.logger.info(f"Workflow apply output {apply_output}")

			show_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_output,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_COMMON_TIMEOUT_SECS),
				heartbeat_timeout=timedelta(seconds=3),
				retry_policy=tf_apply_retry_policy,
			)

		else:
			workflow.upsert_search_attributes({"provisionStatus": ["rejected"]})
			self._current_state = "rejected"
			workflow.logger.info("Workflow apply denied, no work to do.")

		return show_output

	@workflow.signal
	async def signal_approve_apply(self, reason: str="") -> None:
		workflow.logger.info(f"Approval signal received for: {reason}.")
		self._apply_approved = True
		self._signal_reason = reason

	@workflow.signal
	async def signal_deny_apply(self, reason: str="") -> None:
		workflow.logger.info(f"Deny signal received for: {reason}.")
		self._apply_approved = False
		self._signal_reason = reason

	@workflow.query
	def query_signal_reason(self) -> str:
		workflow.logger.info("State query received.")
		return self._current_state

	@workflow.query
	def query_current_state(self) -> str:
		workflow.logger.info("State query received.")
		return self._current_state
