import asyncio
import dataclasses
import logging
import os

from temporalio import converter
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.service import TLSConfig

from codec import CompressionCodec
from shared import PROVISION_INFRA_QUEUE_NAME
from activities import ProvisioningActivities
from workflows import ProvisionInfraWorkflow

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_INFRA_PROVISION_TASK_QUEUE = os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", PROVISION_INFRA_QUEUE_NAME)

async def main() -> None:
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

	# Run the worker
	activities = ProvisioningActivities()

	worker: Worker = Worker(
		client,
		task_queue=TEMPORAL_INFRA_PROVISION_TASK_QUEUE,
		workflows=[ProvisionInfraWorkflow],
		activities=[
			activities.terraform_init,
			activities.terraform_plan,
			activities.terraform_apply,
			activities.terraform_destroy,
			activities.policy_check,
		]
	)
	await worker.run()


if __name__ == "__main__":
	asyncio.run(main())