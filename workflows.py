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

	@workflow.run
	async def run(self, terraform_run_details: TerraformRunDetails) -> str:
		# TODO: add non-retryable errors
		terraform_retry_policy = RetryPolicy(
			maximum_attempts=3,
			maximum_interval=timedelta(seconds=5),
			non_retryable_error_types=[],
		)

		init_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_init,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Workflow init output", init_output)

		plan_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Workflow plan output", plan_output)

		policy_check_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Policy check output", policy_check_output)

		if not policy_check_output:
			await workflow.wait_condition(
				lambda: self._apply_approved is not None
			)

		# If the policy check passed or the apply was approved, apply the changes
		if policy_check_output or self._apply_approved:
			apply_output = await workflow.execute_activity_method(
				ProvisioningActivities.terraform_apply,
				terraform_run_details,
				start_to_close_timeout=timedelta(seconds=TERRAFORM_TIMEOUT_SECS),
				retry_policy=terraform_retry_policy,
			)

			workflow.logger.info("Workflow apply output", apply_output)

	@workflow.signal
	async def approve_apply(self) -> None:
		self._apply_approved = True

	@workflow.signal
	async def cancel_apply(self) -> None:
		self._apply_approved = False