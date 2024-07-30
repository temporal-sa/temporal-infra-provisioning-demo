import subprocess
import os
import json

from temporalio import activity
# TODO
# from temporalio.exceptions import ActivityError

from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformDestroyError, TerraformInitError, TerraformPlanError, \
	TerraformOutputError, PolicyCheckError

class ProvisioningActivities:

	def __init__(self) -> None:
		pass

	def _run_terraform_command(self, command, tf_directory) -> tuple:
		"""Run a Terraform command and capture the output."""

		env = os.environ.copy()
		# TODO: take this as an argument in the run details,
		# TODO: needs to be exported on the worker currently
		secret_env_vars = {
			"TEMPORAL_CLOUD_API_KEY": os.environ.get("TEMPORAL_CLOUD_API_KEY")
		}
		env.update(secret_env_vars)

		process = subprocess.Popen(command, env=env, cwd=tf_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		stdout, stderr = process.communicate()
		return process.returncode, stdout, stderr

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> str:
		"""Initialize the Terraform configuration."""

		activity.logger.info("Terraform init")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init", "-json"], data.directory)
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
		plan_returncode, plan_stdout, plan_stderr = self._run_terraform_command(["terraform", "plan", "-out", tfplan_binary_filename], data.directory)

		if plan_returncode == 0:
			activity.logger.debug(f"Terraform plan succeeded: {plan_stdout}")
		else:
			activity.logger.error(f"Terraform plan failed: {plan_stderr}")
			raise(TerraformPlanError(f"Terraform plan failed: {plan_stderr}"))

		show_returncode, show_stdout, show_stderr = self._run_terraform_command(["terraform", "show", "-json", tfplan_binary_filename], data.directory)
		if show_returncode == 0:
			activity.logger.debug(f"Terraform plan succeeded: {show_stdout}")
		else:
			activity.logger.error(f"Terraform plan failed: {show_stderr}")
			raise(TerraformPlanError(f"Terraform plan failed: {show_stderr}"))

		# TODO: delete the plan file once we get the JSON

		return show_stdout

	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> str:
		"""Apply the Terraform configuration."""

		activity.logger.info("Terraform apply")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "apply", "-json", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
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
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "destroy", "-json", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
		if returncode == 0:
			activity.logger.debug(stdout)
			activity.logger.info(f"Terraform destroy succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform destroy failed: {stderr}")
			raise(TerraformDestroyError(f"Terraform destroy failed: {stderr}"))
		return stdout

	@activity.defn
	async def terraform_output(self, data: TerraformRunDetails) -> int:
		"""Show the output of the Terraform run."""

		activity.logger.info("Terraform destroy")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "output"], data.directory)
		if returncode == 0:
			activity.logger.debug(stdout)
			activity.logger.info(f"Terraform destroy succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform destroy failed: {stderr}")
			raise TerraformOutputError(f"Terraform output failed: {stderr}")
		# return the destroy output as JSON
		return returncode

	@activity.defn
	async def policy_check(self, data: TerraformRunDetails) -> bool:
		"""Evaluate the Terraform plan against a policy."""
		# TODO: check to see if an admin user is being added or a namespace is being delete
		# TODO: use OPA
		policy_passed = False

		activity.logger.info("Policy check (could be external but isn't for now)")
		try:
			plan_json = json.loads(data.plan)
			print(plan_json)
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

