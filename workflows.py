from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError
from shared import TERRAFORM_TIMEOUT_SECS

with workflow.unsafe.imports_passed_through():
	from activities import ProvisioningActivities
	from shared import TerraformRunDetails


@workflow.defn
class ProvisionInfraWorkflow:

	def __init__(self) -> None:
		self._apply_approved = None
		self._current_state = "uninitialized"

	@workflow.run
	async def run(self, terraform_run_details: TerraformRunDetails) -> str:
		# TODO: add non-retryable errors
		terraform_retry_policy = RetryPolicy(
			maximum_attempts=3,
			maximum_interval=timedelta(seconds=5),
			non_retryable_error_types=[],
		)

		self._current_state = "initializing..."
		await workflow.execute_activity_method(
			ProvisioningActivities.terraform_init,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)

		self._current_state = "planning..."
		plan_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)

		terraform_run_details.plan = plan_output

		self._current_state = "checking policy..."
		policy_check_output = await workflow.execute_activity_method(
			ProvisioningActivities.policy_check,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)

		if not policy_check_output:
			self._current_state = "awaiting approval decision..."
			workflow.logger.info("Workflow awaiting approval decision")
			await workflow.wait_condition(
				lambda: self._apply_approved is not None
			)

		# If the policy check passed or the apply was approved, apply the changes
		if policy_check_output or self._apply_approved:
			self._current_state = "applying..."
			apply_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_apply,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
				retry_policy=terraform_retry_policy,
			)
			workflow.logger.info(f"Workflow apply output {apply_output}")
		else:
			self._current_state = "apply denied."
			workflow.logger.info("Workflow apply denied.")
			# TODO: get a handle to the workflow and then cancel it

	@workflow.signal
	async def signal_approve_apply(self) -> None:
		workflow.logger.info("Approve signal received.")
		# TODO: take a "reason" field
		self._apply_approved = True

	@workflow.signal
	async def signal_deny_apply(self) -> None:
		# TODO: take a "reason" field
		workflow.logger.info("Deny signal received.")
		self._apply_approved = False

	@workflow.query
	def current_state_query(self) -> str:
		workflow.logger.info("State query received.")
		return self._current_state
