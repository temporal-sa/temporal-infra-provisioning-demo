import os
import subprocess
import asyncio
from typing import Tuple

from shared import TerraformRunDetails, TerraformApplyError, \
	TerraformInitError, TerraformPlanError, TerraformOutputError, \
	TerraformDestroyError, PolicyCheckError


class TerraformRunner:

	async def _run_cmd_in_dir(self, command: list[str], data: TerraformRunDetails) -> tuple:
		"""Run a Terraform command and capture the output."""

		# Copy the environment variables and update with the provided ones
		env = os.environ.copy()
		env.update(data.env_vars)

		# Run the command in the specified directory
		# Create the subprocess and await its completion
		process = await asyncio.create_subprocess_exec(
			*command,
			env=env,
			cwd=data.directory,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE
		)

		# Read the output (non-blocking)
		stdout_bytes, stderr_bytes = await process.communicate()
		stdout, stderr = stdout_bytes.decode(), stderr_bytes.decode()

		return process.returncode, stdout, stderr

	async def init(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Initialize the Terraform configuration."""

		# Run 'terraform init' command with the '-json' flag
		returncode, stdout, stderr = await self._run_cmd_in_dir(["terraform", "init", "-json"], data)

		if returncode != 0:
			raise TerraformInitError(f"Terraform init errored: {stderr}")

		return stdout, stderr

	async def plan(self, data: TerraformRunDetails, activity_id: str) -> Tuple[str, str, str, str]:
		"""Plan the Terraform configuration."""

		# Get the regular plan output for display purposes
		_, plan_stdout, _ = \
			await self._run_cmd_in_dir(["terraform", "plan"], data)

		# Generate a binary plan file with the provided activity ID
		tfplan_binary_filename = f"{activity_id}.binary"
		plan_returncode, _, plan_stderr = \
			await self._run_cmd_in_dir(["terraform", "plan", "-out", tfplan_binary_filename], data)

		# Remove the binary plan file if there are errors
		if plan_returncode != 0:
			await self._run_cmd_in_dir(["rm", tfplan_binary_filename], data)
			raise TerraformPlanError(f"Terraform plan errored: {plan_stderr}")

		# Show the JSON representation of the plan
		show_json_returncode, show_json_stdout, show_json_stderr = \
			await self._run_cmd_in_dir(["terraform", "show", "-json", tfplan_binary_filename], data)

		# Remove the binary plan file
		await self._run_cmd_in_dir(["rm", tfplan_binary_filename], data)

		if show_json_returncode != 0:
			raise TerraformPlanError(f"Terraform show JSON errored: {show_json_stderr}")

		return show_json_stdout, show_json_stderr, plan_stdout, plan_stderr

	async def apply(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Apply the Terraform configuration."""

		# Apply the Terraform configuration with the '-json' and '-auto-approve' flags
		returncode, stdout, stderr = \
			await self._run_cmd_in_dir(["terraform", "apply", "-json", "-auto-approve"], data)

		if returncode != 0:
			raise TerraformApplyError(f"Terraform apply errored: {stderr}")

		return stdout, stderr

	async def destroy(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Destroy the Terraform configuration."""
		# Destroy the Terraform configuration with the '-json' and '-auto-approve' flags
		returncode, stdout, stderr = \
			await self._run_cmd_in_dir(["terraform", "destroy", "-json", "-auto-approve"], data)

		if returncode != 0:
			raise TerraformDestroyError(f"Terraform destroy errored: {stderr}")

		return stdout, stderr

	async def output(self, data: TerraformRunDetails) -> Tuple[str, str]:
		"""Show the output of the Terraform run."""
		# NOTE: This is a blocking call since it simply returns the output

		# Get the output of the Terraform run in JSON format
		returncode, stdout, stderr = \
			await self._run_cmd_in_dir(["terraform", "output", "-json"], data)

		if returncode != 0:
			raise TerraformOutputError(f"Terraform output errored: {stderr}")

		return stdout, stderr

	async def policy_check(self, data: TerraformRunDetails) -> bool:
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
		"""Set the Terraform plan."""
		self._tfplan = plan
