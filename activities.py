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
		# TODO: return the plan output as Json
		return returncode

	@activity.defn
	async def terraform_apply(self, data: TerraformRunDetails) -> int:
		"""Apply the Terraform configuration."""
		# TODO: get the directory from the details
		print("apply")
		activity.logger.info("Terraform apply")
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "apply", "-auto-approve"], data.directory)
		# TODO: can I do heartbeating here?
		print(stdout)
		if returncode == 0:
			print("Terraform apply succeeded.")
		else:
			print(f"Terraform apply failed: {stderr}")
			# TODO: raise apply err
		# return the apply output as JSON
		return returncode

	@activity.defn
	async def policy_check(self) -> bool:
		# TODO: check to see if an admin user is being added or a namespace is being delete
		print("Policy check (could be external but isn't for now)")
		return False

	"""
	def terraform_show(self) -> str:
		# TODO: make this a signal
		print("Terraform show")

	def terraform_destroy(self) -> str:
		print("Terraform destroy")

	def update_progress(self) -> str:
		# TODO: make this a query
		print("Cost estimation")

	def load_state(self) -> str:
		# TODO: make this a query
		print("load state")

	def archive_state(self) -> str:
		# TODO: make this a query
		print("archive state")
	"""

