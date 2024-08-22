import json
import asyncio

from typing import Tuple
from temporalio import activity
from temporalio.exceptions import ActivityError
from runner import TerraformRunner
from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
		PolicyCheckError, TerraformMissingEnvVarsError, TerraformAPIFailureError


class ProvisioningActivities:

	def __init__(self) -> None:
		self._runner = TerraformRunner()

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> tuple:
		"""Initialize the Terraform configuration."""

		activity.logger.info("Terraform init")
		init_stdout = ""
		init_stderr = ""

		await asyncio.sleep(5)
		activity.logger.info("Sleeping for 5 seconds to slow execution down")

		try:
			init_stdout, init_stderr = await self._runner.init(data)
			activity.logger.debug(f"Terraform init succeeded: {init_stdout}")
		except TerraformInitError as tfie:
			activity.logger.error(f"Terraform init errored: {init_stderr}")
			raise tfie
		except ActivityError as ae:
			activity.logger.error(f"Terraform init errored: {init_stderr}")
			raise ae

		return init_stdout, init_stderr

	@activity.defn
	async def terraform_plan(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Plan the Terraform configuration."""

		# NOTE: cause a recoverable error
		# recoverable_error = 1 / 0
		# TODO: raise exception WorkflowExecutionError("Recoverable error")

		activity.logger.info("Terraform plan")
		plan_json_stdout, plan_json_stderr, plan_stdout, plan_stderr = "", "", "", ""
		activity_id = activity.info().activity_id

		if not data.env_vars:
			activity.logger.debug("Missing environment variables, cannot proceed.")
			raise TerraformMissingEnvVarsError("Missing environment variables, cannot proceed.")

		print("NEILIO", data, data.simulate_api_failure, activity.info().attempt)

		if data.simulate_api_failure and activity.info().attempt < 3:
			raise TerraformAPIFailureError("Terraform cannot reach the API")
		else:
			await asyncio.sleep(5)
			activity.logger.info("Sleeping for 5 seconds to slow execution down")

		try:
			plan_json_stdout, plan_json_stderr, plan_stdout, plan_stderr = await self._runner.plan(data, activity_id)
			self._runner.set_plan(json.loads(plan_json_stdout))
			activity.logger.debug(f"Terraform plan succeeded: {plan_json_stdout}")
		except TerraformPlanError as tfpe:
			activity.logger.error(f"Terraform plan errored: {plan_json_stderr}, {plan_stderr}")
			raise tfpe
		except ActivityError as ae:
			activity.logger.error(f"Terraform plan errored: {plan_json_stderr}, {plan_stderr}")
			raise ae

		return plan_stdout, plan_json_stdout

	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> str:
		"""Apply the Terraform configuration."""

		activity.logger.info("Terraform apply")
		apply_stdout, apply_stderr = "", ""

		try:
			apply_stdout, apply_stderr = await self._runner.apply(data)

			counter = 0
			# NOTE: We want to heartbeat every second to imitate a long running terraform apply
			while counter < 10:
				activity.logger.info("Sleeping for 10 seconds, heartbeating every 1 second")
				activity.heartbeat()
				await asyncio.sleep(1)
				counter += 1

			activity.logger.debug(f"Terraform apply succeeded: {apply_stdout}")
		except TerraformApplyError as tfae:
			activity.logger.error(f"Terraform apply errored: {apply_stderr}")
			raise tfae
		except ActivityError as ae:
			activity.logger.error(f"Terraform apply errored: {apply_stderr}")
			raise ae

		return apply_stdout

	@activity.defn
	async def terraform_output(self, data: TerraformRunDetails) -> str:
		"""Show the output of the Terraform run."""

		activity.logger.info("Terraform output")
		output_stdout, output_stderr = "", ""

		try:
			output_stdout, output_stderr = self._runner.output(data)
			activity.logger.debug(f"Terraform output succeeded: {output_stdout}")
		except TerraformOutputError as tfoe:
			activity.logger.error(f"Terraform output errored: {output_stderr}")
			raise tfoe
		except ActivityError as ae:
			activity.logger.error(f"Terraform output errored: {output_stderr}")
			raise ae

		return output_stdout

	@activity.defn
	async def policy_check(self, data: TerraformRunDetails) -> bool:
		"""Evaluate the Terraform plan against a policy. In this case, we're
		checking for admin users being added at the account level."""

		activity.logger.info("Policy check (could be external but isn't for now)")
		policy_passed = False

		await asyncio.sleep(5)
		activity.logger.info("Sleeping for 5 seconds to slow execution down")

		try:
			policy_passed = self._runner.policy_check(data)
		except PolicyCheckError as pce:
			activity.logger.error(f"Policy check errored: {pce}")
			raise pce
		except ActivityError as ae:
			activity.logger.error(f"Policy check errored: {ae}")
			raise ae

		return policy_passed

	"""
	def load_state(self) -> str:
		activity.logger.info("load state")

	def archive_state(self) -> str:
		activity.logger.info("archive state")
	"""
