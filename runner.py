import os
import subprocess

from typing import Tuple
from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
		PolicyCheckError


class TerraformRunner:

	# TODO: can I instantiate these?
	def _run_cmd_in_dir(self, command: list[str], data: TerraformRunDetails) -> tuple:
		"""Run a Terraform command and capture the output."""

		env = os.environ.copy()
		env.update(data.env_vars)

		process = subprocess.Popen(command, env=env, cwd=data.directory, \
			stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		stdout, stderr = process.communicate()

		return process.returncode, stdout, stderr

	async def init(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Initialize the Terraform configuration."""

		returncode, stdout, stderr = self._run_cmd_in_dir(["terraform", "init"], data)

		if returncode != 0:
			raise TerraformInitError(f"Terraform init errored: {stderr}")
		return stdout, stderr

	async def plan(self, data: TerraformRunDetails, activity_id: str) -> Tuple[str, str, str]:
		"""Plan the Terraform configuration."""

		tfplan_binary_filename = f"{activity_id}.binary"
		plan_returncode, _, plan_stderr = \
			self._run_cmd_in_dir(["terraform", "plan", "-out", tfplan_binary_filename], data)

		# No need to handle any errors for removing the binary file
		if plan_returncode != 0:
			self._run_cmd_in_dir(["rm", tfplan_binary_filename], data)
			raise TerraformPlanError(f"Terraform plan errored: {plan_stderr}")

		show_json_returncode, show_json_stdout, show_json_stderr \
			= self._run_cmd_in_dir(["terraform", "show", "-json", tfplan_binary_filename], data)

		if show_json_returncode != 0:
			self._run_cmd_in_dir(["rm", tfplan_binary_filename], data)
			raise TerraformPlanError(f"Terraform show JSON errored: {show_json_stderr}")

		self._run_cmd_in_dir(["rm", tfplan_binary_filename], data)

		return show_json_stdout, show_json_stderr, plan_stderr

	async def apply(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Apply the Terraform configuration."""

		# TODO: add a flag to use auto-approve instead of opting in?
		returncode, stdout, stderr = \
			self._run_cmd_in_dir(["terraform", "apply", "-json", "-auto-approve"], data)

		if returncode != 0:
			raise TerraformApplyError(f"Terraform apply errored: {stderr}")

		return stdout, stderr

	def output(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Show the output of the Terraform run."""
		# NOTE: This is a blocking call since it simply returns the output
		# TODO: make notes like this in every comment

		returncode, stdout, stderr = \
			self._run_cmd_in_dir(["terraform", "output"], data)

		if returncode != 0:
			raise TerraformOutputError(f"Terraform output errored: {stderr}")

		return stdout, stderr

	def policy_check(self, data: TerraformRunDetails) -> bool:
		"""Evaluate the Terraform plan against a policy. In this case, we're
		checking for admin users being added at the account level."""
		# NOTE: This is a blocking call since it simply checks a JSON file

		policy_passed = True

		try:
			planned_changes = self._tfplan["resource_changes"]
			for planned_change in planned_changes:
				resource_type = planned_change["type"]
				if resource_type == "temporalcloud_user":
					actions = planned_change["change"]["actions"]
					if "create" in actions:
						expected_after_access = planned_change["change"]["after"]["account_access"]
						if expected_after_access == "admin":
							policy_passed = False
							continue
		except Exception as e:
			raise PolicyCheckError(f"Policy check errored: {e}")

		return policy_passed

	def set_plan(self, plan: dict) -> None:
		self._tfplan = plan

	"""
	def load_state(self) -> str:
		activity.logger.info("load state")

	def archive_state(self) -> str:
		activity.logger.info("archive state")
	"""

