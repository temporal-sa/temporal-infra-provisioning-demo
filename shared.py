import os
import dataclasses

from dataclasses import dataclass, field
from typing import Dict
from temporalio.client import Client
from temporalio.service import  TLSConfig
from temporalio import converter
from codec import CompressionCodec

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')

async def get_temporal_client() -> Client:
	tls_config = None

	if TEMPORAL_MTLS_TLS_CERT != "" and TEMPORAL_MTLS_TLS_KEY != "":
		with open(TEMPORAL_MTLS_TLS_CERT, "rb") as f:
			client_cert = f.read()

		with open(TEMPORAL_MTLS_TLS_KEY, "rb") as f:
			client_key = f.read()

		tls_config = TLSConfig(
			domain=TEMPORAL_HOST_URL.split(":")[0],
			client_cert=client_cert,
			client_private_key=client_key,
		)

	if ENCRYPT_PAYLOADS:
		client: Client = await Client.connect(
			TEMPORAL_HOST_URL,
			namespace=TEMPORAL_NAMESPACE,
			tls=tls_config if tls_config else False,
			data_converter=dataclasses.replace(
				converter.default(),
				payload_codec=CompressionCodec(),
				failure_converter_class=converter.DefaultFailureConverterWithEncodedAttributes
			),
		)
	else:
		client: Client = await Client.connect(
			TEMPORAL_HOST_URL,
			namespace=TEMPORAL_NAMESPACE,
			tls=tls_config if tls_config else False,
		)

	return client

@dataclass
class TerraformRunDetails:
	directory: str
	id: str = ""
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
class PolicyCheckError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

"""
@dataclasse
class LoadStatefileError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.message)

@dataclass
class ArchiveStatefileError(Exception):
	def __init__(self, message) -> None:
		self.message: str = message
		super().__init__(self.messag)
"""
