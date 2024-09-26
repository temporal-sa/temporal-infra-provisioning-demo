import json
import asyncio

from typing import Tuple
from temporalio import activity
from temporalio.exceptions import ActivityError
from runner import TerraformRunner
from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
	PolicyCheckError, TerraformMissingEnvVarsError, TerraformAPIFailureError, \
	TerraformDestroyError, TerraformRecoverableError


class ProvisioningActivities:

	def __init__(self) -> None:
		self._runner = TerraformRunner()

	# Heartbeat function to be run concurrently
	async def _heartbeat(self, duration: int=1):
		while True:
			activity.logger.info(f"Sleeping for {duration} second(s) then heartbeating")
			activity.heartbeat("Sending heartbeat...")
			await asyncio.sleep(duration)

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> tuple:
		"""Initialize the Terraform configuration."""

		activity.logger.info("Terraform init")
		init_stdout = ""
		init_stderr = ""

		await asyncio.sleep(3)
		activity.logger.info("Sleeping for 3 seconds to slow execution down")

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
	async def terraform_plan(self, data: TerraformRunDetails) -> tuple:
		"""Plan the Terraform configuration."""

		# NOTE: uncomment to cause a recoverable error
		# raise TerraformRecoverableError("This is a recoverable error")

		activity.logger.info("Terraform plan")
		plan_json_stdout, plan_json_stderr, plan_stdout, plan_stderr = "", "", "", ""
		activity_id = activity.info().activity_id

		if not data.env_vars:
			activity.logger.debug("Missing environment variables, cannot proceed.")
			raise TerraformMissingEnvVarsError("Missing environment variables, cannot proceed.")
			# TODO: raise ApplicationError?

		if data.simulate_api_failure and activity.info().attempt < 5:
			raise TerraformAPIFailureError("Terraform cannot reach the API")
		else:
			await asyncio.sleep(3)
			activity.logger.info("Sleeping for 3 seconds to slow execution down")

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
			heartbeat_task = asyncio.create_task(self._heartbeat())
			runner_apply_task = asyncio.create_task(self._runner.apply(data))

			# Await the apply task
			apply_stdout, apply_stderr = await runner_apply_task

			# Cancel the heartbeat task after the long task completes
			heartbeat_task.cancel()

			try:
				# Wait for the heartbeat task to fully cancel
				await heartbeat_task
			except asyncio.CancelledError:
				activity.logger.debug("Apply heartbeat cancelled.")

			activity.logger.debug(f"Terraform apply succeeded: {apply_stdout}")
		except TerraformApplyError as tfae:
			activity.logger.error(f"Terraform apply errored: {apply_stderr}")
			raise tfae
		except ActivityError as ae:
			activity.logger.error(f"Terraform apply errored: {apply_stderr}")
			raise ae

		return apply_stdout

	@activity.defn
	async def terraform_output(self, data: TerraformRunDetails) -> dict:
		"""Show the output of the Terraform run."""

		activity.logger.info("Terraform output")
		output_stdout, output_stderr = "", ""

		try:
			output_stdout, output_stderr = await self._runner.output(data)
			activity.logger.debug(f"Terraform output succeeded: {output_stdout}")
		except TerraformOutputError as tfoe:
			activity.logger.error(f"Terraform output errored: {output_stderr}")
			raise tfoe
		except ActivityError as ae:
			activity.logger.error(f"Terraform output errored: {output_stderr}")
			raise ae

		return json.loads(output_stdout)

	@activity.defn
	async def terraform_destroy(self, data: TerraformRunDetails) -> str:
		"""Destroy the Terraform configuration."""

		activity.logger.info("Terraform destroy")
		destroy_stdout, destroy_stderr = "", ""

		try:
			heartbeat_task = asyncio.create_task(self._heartbeat())
			runner_destroy_task = asyncio.create_task(self._runner.destroy(data))

			# Await the destroy task
			destroy_stdout, destroy_stderr = await runner_destroy_task

			# Cancel the heartbeat task after the long task completes
			heartbeat_task.cancel()

			try:
				# Wait for the heartbeat task to fully cancel
				await heartbeat_task
			except asyncio.CancelledError:
				activity.logger.debug("Destroy heartbeat cancelled.")

			activity.logger.debug(f"Terraform destroy succeeded: {destroy_stdout}")
		except TerraformApplyError as tfae:
			activity.logger.error(f"Terraform destroy errored: {destroy_stderr}")
			raise tfae
		except ActivityError as ae:
			activity.logger.error(f"Terraform destroy errored: {destroy_stderr}")
			raise ae

		return destroy_stdout

	@activity.defn
	async def policy_check(self, data: TerraformRunDetails) -> bool:
		"""Evaluate the Terraform plan against a policy. In this case, we're
		checking for admin users being added at the account level."""

		activity.logger.info("Policy check (could be external but isn't for now)")
		policy_passed = False

		await asyncio.sleep(3)
		activity.logger.info("Sleeping for 3 seconds to slow execution down")

		try:
			policy_passed = await self._runner.policy_check(data)
		except PolicyCheckError as pce:
			activity.logger.error(f"Policy check errored: {pce}")
			raise pce
		except ActivityError as ae:
			activity.logger.error(f"Policy check errored: {ae}")
			raise ae

		return policy_passed
