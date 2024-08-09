from temporalio.client import Client
from temporalio.service import  TLSConfig
from temporalio import converter
from codec import CompressionCodec

import os
import dataclasses

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')

async def get():
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
