import subprocess
import os

from temporalio import activity
# TODO
# from temporalio.exceptions import ActivityError

from shared import TerraformRunDetails

## TODO: use activity logger
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
	async def terraform_init(self, data: TerraformRunDetails) -> int:
		"""Initialize the Terraform configuration."""
		# TODO: get the directory from the details
		activity.logger.info("Terraform init")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init"], data.directory)
		if returncode == 0:
			activity.logger.info(f"Terraform init succeeded: {stdout}")
		else:
			activity.logger.error(f"Terraform init failed: {stderr}")
			# TODO: raise init err
		return returncode

	@activity.defn
	async def terraform_plan(self, data: TerraformRunDetails) -> int:
		"""Plan the Terraform configuration."""
		# TODO: get the directory from the details
		activity.logger.info("Terraform plan")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init"], data.directory)
		if returncode == 0:
			activity.logger.info(f"Terraform plan succeeded: {stdout}")
		else:
			activity.logger.error(f"Terraform plan failed: {stderr}")
			# TODO: raise plan err
		# TODO: return the plan output as Json
		return returncode

	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> int:
		"""Apply the Terraform configuration."""
		# TODO: get the directory from the details
		activity.logger.info("Terraform apply")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "apply", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
		if returncode == 0:
			activity.logger.info(f"Terraform apply succeeded: {stdout}")
		else:
			activity.logger.error(f"Terraform apply failed: {stderr}")
			# TODO: raise apply err
		# return the apply output as JSON
		return returncode

	@activity.defn
	async def terraform_destroy(self, data: TerraformRunDetails) -> int:
		"""Destroy the Terraform configuration."""
		# TODO: get the directory from the details
		activity.logger.info("Terraform destroy")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "destroy", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
		if returncode == 0:
			activity.logger.info(stdout)
			activity.logger.info(f"Terraform destroy succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform destroy failed: {stderr}")
			# TODO: raise destroy err
		# return the destroy output as JSON
		return returncode

	@activity.defn
	async def terraform_output(self, data: TerraformRunDetails) -> int:
		"""Show the output of the Terraform run."""
		# TODO: get the directory from the details
		activity.logger.info("Terraform destroy")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "destroy", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
		if returncode == 0:
			activity.logger.info(stdout)
			activity.logger.info(f"Terraform destroy succeeded: {stdout}")
		else:
			activity.logger.info(f"Terraform destroy failed: {stderr}")
			# TODO: raise destroy err
		# return the destroy output as JSON
		return returncode

	@activity.defn
	async def policy_check(self, data: TerraformRunDetails, plan: str) -> bool:
		"""Evaluate the Terraform plan against a policy."""
		# TODO: check to see if an admin user is being added or a namespace is being delete
		activity.logger.info("Policy check (could be external but isn't for now)")
		print("CHECK THE PLAN AND FAIL THE POLICY")
		return False

	"""
	def load_state(self) -> str:
		activity.logger.info("load state")

	def archive_state(self) -> str:
		activity.logger.info("archive state")
	"""

