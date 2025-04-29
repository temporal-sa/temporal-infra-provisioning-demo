import os
import dataclasses
from dataclasses import dataclass, field
from typing import Dict, Optional
from typing_extensions import runtime
from temporalio.client import Client
from temporalio.service import  TLSConfig
from temporalio import converter
from temporalio.runtime import Runtime

from shared.codec import CompressionCodec, EncryptionCodec

# Get the Temporal host URL from environment variable, default to "localhost:7233" if not set
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")

# Get the mTLS TLS certificate and key file paths from environment variables
TEMPORAL_TLS_CERT = os.environ.get("TEMPORAL_TLS_CERT", "")
TEMPORAL_TLS_KEY = os.environ.get("TEMPORAL_TLS_KEY", "")

# Get the Temporal namespace from environment variable, default to "default" if not set
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

# Get the Temporal task queue from environment variable, default to "provision-infra" if not set
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

# Get the Temporal Cloud API key from environment variable
TEMPORAL_API_KEY = os.environ.get("TEMPORAL_API_KEY", "")

# Determine if payloads should be encrypted based on the value of the "ENCRYPT_PAYLOADS" environment variable
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')

# Set the Terraform common timeout in seconds
TERRAFORM_COMMON_TIMEOUT_SECS = 300


async def get_temporal_client(runtime: Optional[Runtime] = None) -> Client:
	tls_config = False
	data_converter = None

	# If mTLS TLS certificate and key are provided, create a TLSConfig object
	if TEMPORAL_TLS_CERT != "" and TEMPORAL_TLS_KEY != "":
		with open(TEMPORAL_TLS_CERT, "rb") as f:
			client_cert = f.read()

		with open(TEMPORAL_TLS_KEY, "rb") as f:
			client_key = f.read()

		tls_config = TLSConfig(
			client_cert=client_cert,
			client_private_key=client_key,
		)

	if ENCRYPT_PAYLOADS:
		print("Using encryption codec")
		data_converter = dataclasses.replace(
			converter.default(),
			payload_codec=EncryptionCodec(),
			failure_converter_class=converter.DefaultFailureConverterWithEncodedAttributes
		)

	if TEMPORAL_API_KEY != "":
		print(f"Using Cloud API key: XXX...{TEMPORAL_API_KEY[-5:]}")
		# Create a Temporal client using the Cloud API key
		client = await Client.connect(
			TEMPORAL_ADDRESS,
			namespace=TEMPORAL_NAMESPACE,
			rpc_metadata={"temporal-namespace": TEMPORAL_NAMESPACE},
			api_key=TEMPORAL_API_KEY,
			data_converter=data_converter,
			tls=True,
			runtime=runtime
		)
	else:
		print("Using MTLS")
		# Create a Temporal client using MTLS
		client: Client = await Client.connect(
			TEMPORAL_ADDRESS,
			namespace=TEMPORAL_NAMESPACE,
			tls=tls_config,
			data_converter=data_converter,
			runtime=runtime
		)

	return client

@dataclass
class TerraformRunDetails:
	directory: str
	id: str = ""
	plan: str = ""
	env_vars: Dict[str, str] = field(default_factory=dict)
	apply_timeout_secs: int = 300
	include_custom_search_attrs: bool = True
	ephemeral: bool = False
	ephemeral_ttl: int = 15
	soft_fail_policy: bool = False
	hard_fail_policy: bool = False
	simulate_api_failure: bool = False

@dataclass
class ApplyDecisionDetails:
	is_approved: bool
	reason: str = ""

@dataclass
class TerraformMissingEnvVarsError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformRecoverableError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class TerraformAPIFailureError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)


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

@dataclass
class TerraformOutputError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)
