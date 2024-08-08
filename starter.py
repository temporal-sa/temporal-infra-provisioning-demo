import asyncio
import dataclasses
import uuid
import logging
import os

from temporalio import converter
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair
from temporalio.client import Client
from temporalio.service import TLSConfig

from codec import CompressionCodec
from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')

async def main():
	logging.basicConfig(level=logging.INFO)

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

	tcloud_tf_dir = "./terraform"
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY
	}

	run_1 = TerraformRunDetails(
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars
	)

	# Execute a workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")

	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		run_1,
		id=f"infra-provisioning-run-{uuid.uuid4()}",
		task_queue=TEMPORAL_TASK_QUEUE,
		search_attributes=TypedSearchAttributes([
			SearchAttributePair(provision_status_key, "uninitialized"),
			SearchAttributePair(tf_directory_key, tcloud_tf_dir)
		]),
	)

	result = await handle.result()

	print(f"Result: {result}")


if __name__ == "__main__":
	asyncio.run(main())
