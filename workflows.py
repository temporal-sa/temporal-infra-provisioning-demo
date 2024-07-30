from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
	from activities import ProvisioningActivities
	from shared import TerraformRunDetails

@workflow.defn
class ProvisionInfraWorkflow:
	@workflow.run

	async def run(self, terraform_run_details: TerraformRunDetails) -> str:
		# TODO: add non-retryable errors
		terraform_retry_policy = RetryPolicy(
			maximum_attempts=3,
			maximum_interval=timedelta(seconds=2),
			non_retryable_error_types=[],
		)

		init_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_init,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=10),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Workflow init output", init_output)

		plan_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_plan,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=10),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Workflow plan output", plan_output)

		apply_output = await workflow.execute_activity_method(
			ProvisioningActivities.terraform_apply,
			terraform_run_details,
			start_to_close_timeout=timedelta(seconds=10),
			retry_policy=terraform_retry_policy,
		)
		workflow.logger.info("Workflow apply output", apply_output)
