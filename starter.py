import asyncio
import uuid
import logging
import os

from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, PROVISION_INFRA_QUEUE_NAME
from temporalio.client import Client
from temporalio.service import TLSConfig

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_INFRA_PROVISION_TASK_QUEUE = os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", PROVISION_INFRA_QUEUE_NAME)
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")


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

	client: Client = await Client.connect(
		TEMPORAL_HOST_URL,
		namespace=TEMPORAL_NAMESPACE,
		tls=tls_config if tls_config else False
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
	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		run_1,
		id=f"infra-provisioning-run-{uuid.uuid4()}",
		task_queue=TEMPORAL_INFRA_PROVISION_TASK_QUEUE,
		# TODO: add the directory as a custom attribute
	)

	print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")

	result = await handle.result()

	print(f"Result: {result}")


if __name__ == "__main__":
	asyncio.run(main())
