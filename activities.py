import subprocess
import os
import json
import asyncio
from temporalio import activity
# TODO: use activity errors
# from temporalio.exceptions import ActivityError

from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
		TerraformDestroyError, PolicyCheckError

class ProvisioningActivities:

	def __init__(self) -> None:
		pass

	def _run_cmd_in_tf_dir(self, command: list[str], data: TerraformRunDetails) -> tuple:
		"""Run a Terraform command and capture the output."""
		env = os.environ.copy()
		env.update(data.env_vars)
		process = subprocess.Popen(command, env=env, cwd=data.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		stdout, stderr = process.communicate()
		return process.returncode, stdout, stderr

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> str:
		"""Initialize the Terraform configuration."""

		activity.logger.info("Terraform init")
		returncode, stdout, stderr = self._run_cmd_in_tf_dir(["terraform", "init", "-json"], data)
		if returncode == 0:
			activity.logger.debug(f"Terraform init succeeded: {stdout}")
		else:
			activity.logger.error(f"Terraform init failed: {stderr}")
			raise(TerraformInitError(f"Terraform init failed: {stderr}"))
		return stdout

	@activity.defn
	async def terraform_plan(self, data: TerraformRunDetails) -> str:
		"""Plan the Terraform configuration."""

		activity.logger.info("Terraform plan")
		tfplan_binary_filename = "tfplan.binary"

		# TODO: change the file name of the plan since this can be shared?
		plan_returncode, plan_stdout, plan_stderr = self._run_cmd_in_tf_dir(["terraform", "plan", "-out", tfplan_binary_filename], data)

		await asyncio.sleep(3)
		# TODO: heartbeating, note in the docs that this can take a while

		if plan_returncode == 0:
			activity.logger.debug(f"Terraform plan succeeded: {plan_stdout}")
		else:
			activity.logger.error(f"Terraform plan failed: {plan_stderr}")
			raise(TerraformPlanError(f"Terraform plan failed: {plan_stderr}"))

		show_returncode, show_stdout, show_stderr = self._run_cmd_in_tf_dir(["terraform", "show", "-json", tfplan_binary_filename], data)
		if show_returncode == 0:
			activity.logger.debug(f"Terraform plan succeeded: {show_stdout}")
		else:
			activity.logger.error(f"Terraform plan failed: {show_stderr}")
			raise(TerraformPlanError(f"Terraform plan failed: {show_stderr}"))

		# NOTE: no need to handle any errors, the file is removed or nonexistent
		self._run_cmd_in_tf_dir(["rm", tfplan_binary_filename], data)

		return show_stdout

	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> str:
		"""Apply the Terraform configuration."""

		activity.logger.info("Terraform apply")

		returncode, stdout, stderr = self._run_cmd_in_tf_dir(["terraform", "apply", "-json", "-auto-approve"], data)

		await asyncio.sleep(3)
		# TODO: heartbeating, note in the docs that this can take a while

		if returncode == 0:
			activity.logger.debug(f"Terraform apply succeeded: {stdout}")
		else:
			activity.logger.error(f"Terraform apply failed: {stderr}")
			raise(TerraformApplyError(f"Terraform apply failed: {stderr}"))

		return stdout

	@activity.defn
	async def terraform_destroy(self, data: TerraformRunDetails) -> str:
		"""Destroy the Terraform configuration."""

		activity.logger.info("Terraform destroy")
		returncode, stdout, stderr = self._run_cmd_in_tf_dir(["terraform", "destroy", "-json", "-auto-approve"], data)
		# TODO: heartbeating, note in the docs that this can take a while
		if returncode == 0:
			activity.logger.debug(f"Terraform destroy succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform destroy failed: {stderr}")
			raise(TerraformDestroyError(f"Terraform destroy failed: {stderr}"))
		return stdout

	@activity.defn
	async def terraform_output(self, data: TerraformRunDetails) -> int:
		"""Show the output of the Terraform run."""

		activity.logger.info("Terraform output")
		returncode, stdout, stderr = self._run_cmd_in_tf_dir(["terraform", "output"], data)
		if returncode == 0:
			activity.logger.debug(f"Terraform output succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform output failed: {stderr}")
			raise TerraformOutputError(f"Terraform output failed: {stderr}")
		# return the destroy output as JSON
		return returncode

	@activity.defn
	async def policy_check(self, data: TerraformRunDetails) -> bool:
		"""Evaluate the Terraform plan against a policy. In this case, we're
		checking for admin users being added at the account level."""

		# TODO: check namespace is being deleted, use OPA
		policy_passed = True

		activity.logger.info("Policy check (could be external but isn't for now)")
		try:
			planned_changes = json.loads(data.plan)["resource_changes"]
			for planned_change in planned_changes:
				resource_type = planned_change["type"]
				if resource_type == "temporalcloud_user":
					actions = planned_change["change"]["actions"]
					if "create" in actions:
						expected_after_access = planned_change["change"]["after"]["account_access"]
						if expected_after_access == "admin":
							activity.logger.info("Admin user being created, policy check failed, must be approved manually")
							policy_passed = False
							continue
		except Exception as e:
			# TODO: activity error or just a raw exception?
			raise PolicyCheckError(f"Policy check failed: {e}")

		return policy_passed

	"""
	def load_state(self) -> str:
		activity.logger.info("load state")

	def archive_state(self) -> str:
		activity.logger.info("archive state")
	"""

