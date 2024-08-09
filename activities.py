import json
import asyncio
from temporalio import activity
from temporalio.exceptions import ActivityError

from runner import TerraformRunner
from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
		PolicyCheckError


class ProvisioningActivities:

	def __init__(self) -> None:
		self._runner = TerraformRunner()

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> tuple:
		"""Initialize the Terraform configuration."""

		activity.logger.info("Terraform init")
		init_stdout = ""
		init_stderr = ""

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
	async def terraform_plan(self, data: TerraformRunDetails) -> str:
		"""Plan the Terraform configuration."""

		activity.logger.info("Terraform plan")
		show_json_stdout, show_json_stderr, show_plan_stderr = "", "", ""
		activity_id = activity.info().activity_id

		try:
			show_json_stdout, show_json_stderr, show_plan_stderr = await self._runner.plan(data, activity_id)
			self._runner.set_plan(json.loads(show_json_stdout))
			activity.logger.debug(f"Terraform plan succeeded: {show_json_stdout}")
		except TerraformPlanError as tfpe:
			activity.logger.error(f"Terraform plan errored: {show_plan_stderr}, {show_json_stderr}")
			raise tfpe
		except ActivityError as ae:
			activity.logger.error(f"Terraform plan errored: {show_plan_stderr}, {show_json_stderr}")
			raise ae

		return show_json_stdout

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
