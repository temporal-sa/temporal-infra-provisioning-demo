import asyncio
import uuid
import logging
import os

from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, PROVISION_INFRA_QUEUE_NAME
from temporalio.client import Client

# TODO: use these
TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", None)
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", None)
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_INFRA_PROVISION_TASK_QUEUE = os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", PROVISION_INFRA_QUEUE_NAME)
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", None)


async def main():
	logging.basicConfig(level=logging.INFO)

	# Create client connected to server at the given address
	# TODO: take host as an arg / config item
	client = await Client.connect(TEMPORAL_HOST_URL)

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
