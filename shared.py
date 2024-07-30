from dataclasses import dataclass

PROVISION_INFRA_QUEUE_NAME = "PROVISION_INFRA_QUEUE"

@dataclass
class TerraformRunDetails:
	directory: str
	# module_name

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
class TerraformDestroyError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)