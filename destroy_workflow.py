from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from shared import TERRAFORM_COMMON_TIMEOUT_SECS

with workflow.unsafe.imports_passed_through():
	from activities import ProvisioningActivities
	from shared import TerraformRunDetails



@workflow.defn
class DeprovisionInfraWorkflow:

	def __init__(self) -> None:
		self._apply_approved = None
		self._tf_run_details = None
		self._current_status = "uninitialized"
		self._progress = 0
		self._tf_plan_output = ""

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
		self._progress = 33
		self._current_status = "initialized"

		tf_apply_destroy_retry_policy = RetryPolicy(
			initial_interval=timedelta(seconds=3),
			maximum_interval=timedelta(seconds=5),
			maximum_attempts=100,
			non_retryable_error_types=[],
		)
		self._progress = 66
		self._current_status = "destroying"
		await workflow.execute_activity_method(
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
