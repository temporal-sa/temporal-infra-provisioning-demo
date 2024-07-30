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
		print(secret_env_vars)
		env.update(secret_env_vars)

		process = subprocess.Popen(command, env=env, cwd=tf_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		stdout, stderr = process.communicate()
		return process.returncode, stdout, stderr

	@activity.defn
	async def terraform_init(self, data: TerraformRunDetails) -> int:
		"""Initialize the Terraform configuration."""
		# TODO: get the directory from the details
		print("init")
		activity.logger.info("Terraform init")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init"], data.directory)
		print(stdout)
		if returncode == 0:
			print("Terraform init succeeded.")
		else:
			print(f"Terraform init failed: {stderr}")
			# TODO: raise init err
		return returncode

	@activity.defn
	async def terraform_plan(self, data: TerraformRunDetails) -> int:
		"""Initialize the Terraform configuration."""
		# TODO: get the directory from the details
		print("plan")
		activity.logger.info("Terraform plan")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init"], data.directory)
		print(stdout)
		if returncode == 0:
			print("Terraform plan succeeded.")
		else:
			print(f"Terraform plan failed: {stderr}")
			# TODO: raise plan err
		return returncode


	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> int:
		"""Apply the Terraform configuration."""
		# TODO: get the directory from the details
		print("apply")
		activity.logger.info("Terraform apply")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "apply", "-auto-approve"], data.directory)
		print(stdout)
		if returncode == 0:
			print("Terraform apply succeeded.")
		else:
			print(f"Terraform apply failed: {stderr}")
			# TODO: raise apply err
		return returncode

	"""
	def terraform_plan(self) -> str:
		print("terraform plan")

	def terraform_output(self) -> str:
		print("Terraform output")

	def terraform_destroy(self) -> str:
		print("Terraform destroy")

	def policy_check(self) -> str:
		print("Policy check")

	def cost_estimation(self) -> str:
		print("Cost estimation")

	def approve_plan(self) -> str:
		print("Cost estimation")

	def update_progress(self) -> str:
		print("Cost estimation")
	"""

