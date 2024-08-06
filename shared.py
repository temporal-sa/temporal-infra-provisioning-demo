from dataclasses import dataclass, field
from typing import Dict
from enum import Enum
from temporalio.common import SearchAttributeKey

# NOTE: for init, policy_check, plan and outputs, they shouldn't take longer
# than 30 seconds.
TERRAFORM_COMMON_TIMEOUT_SECS = 30
PROVISION_INFRA_QUEUE_NAME = "PROVISION_INFRA_QUEUE"

PROVISION_STATUS_KEY = SearchAttributeKey.for_bool("provision_status")
TF_DIRECTORY_KEY = SearchAttributeKey.for_bool("terraform_directory")

@dataclass
class TerraformRunDetails:
	directory: str
	plan: str = ""
	env_vars: Dict[str, str] = field(default_factory=dict)
	apply_timeout_secs: int = 30

@dataclass
class TerraformInitError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformPlanError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformApplyError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformOutputError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformDestroyError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

# TODO: make this OPA and use it in the policy check activity
@dataclass
class PolicyCheckError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

"""
TODO: use these or remove them
@dataclass
class LoadStatefileError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class ArchiveStatefileError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)
"""