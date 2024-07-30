import subprocess

from temporalio import activity
# TODO
# from temporalio.exceptions import ActivityError

from shared import TerraformRunDetails

## TODO: use activity logger
class ProvisioningActivities:

	def __init__(self, tf_directory=None) -> None:
		self._tf_directory = tf_directory

	def _run_terraform_command(self, command):
		"""Run a Terraform command and capture the output."""
		process = subprocess.Popen(command, cwd=self._tf_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		stdout, stderr = process.communicate()
		return process.returncode, stdout, stderr

	@activity.defn
	def terraform_init(self, data: TerraformRunDetails) -> str:
		"""Initialize the Terraform configuration."""
		"""
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "init"])
		print(stdout)
		if returncode == 0:
			print("Terraform init succeeded.")
		else:
			print(f"Terraform init failed: {stderr}")
			# TODO: raise init err
		return returncode
		"""
		# TODO: get the directory from the details
		activity.logger.info("Terraform init")

	@activity.defn
	def terraform_apply(self, data: TerraformRunDetails) -> str:
		"""Apply the Terraform configuration."""
		"""
		returncode, stdout, stderr = self._run_terraform_command(["terraform", "apply", "-auto-approve"])
		print(stdout)
		if returncode == 0:
			print("Terraform apply succeeded.")
		else:
			print(f"Terraform apply failed: {stderr}")
			# TODO: raise apply err
		return returncode
		"""
		# TODO: get the directory from the details
		activity.logger.info("Terraform apply")

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



