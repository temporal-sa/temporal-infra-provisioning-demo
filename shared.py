import os
import dataclasses
from dataclasses import dataclass, field
from typing import Dict
from typing_extensions import runtime
from temporalio.client import Client
from temporalio.service import  TLSConfig
from temporalio import converter
from temporalio.runtime import Runtime

from codec import CompressionCodec, EncryptionCodec

# Get the Temporal host URL from environment variable, default to "localhost:7233" if not set
TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")

# Get the mTLS TLS certificate and key file paths from environment variables
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")

# Get the Temporal namespace from environment variable, default to "default" if not set
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

# Get the Temporal task queue from environment variable, default to "provision-infra" if not set
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

# Get the Temporal Cloud API key from environment variable
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")

# Determine if payloads should be encrypted based on the value of the "ENCRYPT_PAYLOADS" environment variable
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')


async def get_temporal_client(runtime: Runtime=None) -> Client:
	tls_config = False

	# If mTLS TLS certificate and key are provided, create a TLSConfig object
	if TEMPORAL_MTLS_TLS_CERT != "" and TEMPORAL_MTLS_TLS_KEY != "":
		with open(TEMPORAL_MTLS_TLS_CERT, "rb") as f:
			client_cert = f.read()

		with open(TEMPORAL_MTLS_TLS_KEY, "rb") as f:
			client_key = f.read()

		tls_config = TLSConfig(
			client_cert=client_cert,
			client_private_key=client_key,
		)

	if ENCRYPT_PAYLOADS:
		# Create a Temporal client with encryption codec for payloads
		client: Client = await Client.connect(
			TEMPORAL_HOST_URL,
			namespace=TEMPORAL_NAMESPACE,
			tls=tls_config,
			data_converter=dataclasses.replace(
				converter.default(),
				payload_codec=EncryptionCodec(),
				failure_converter_class=converter.DefaultFailureConverterWithEncodedAttributes
			),
			runtime=runtime
		)
	else:
		# Create a regular Temporal client
		client: Client = await Client.connect(
			TEMPORAL_HOST_URL,
			namespace=TEMPORAL_NAMESPACE,
			tls=tls_config,
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
class TerraformOutputError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class PolicyCheckError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)
