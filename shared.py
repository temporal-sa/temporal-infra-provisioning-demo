from dataclasses import dataclass, field
from typing import Dict

PROVISION_INFRA_QUEUE_NAME = "PROVISION_INFRA_QUEUE"
TERRAFORM_TIMEOUT_SECS = 300

@dataclass
class TerraformRunDetails:
	directory: str
	# TODO: use a dict?
	plan: str = ""
	env_vars: Dict[str, str] = field(default_factory=dict)


# TODO: do I need all of these inits?
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
class PolicyCheckError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformDestroyError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformOutputError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

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
