import asyncio
import uuid
import logging
import os

from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, PROVISION_INFRA_QUEUE_NAME
from temporalio.client import Client

# TODO: use these
TEMPORAL_HOST_URL=os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT=os.environ.get("TEMPORAL_MTLS_TLS_CERT", None)
TEMPORAL_MTLS_TLS_KEY=os.environ.get("TEMPORAL_MTLS_TLS_KEY", None)
TEMPORAL_NAMESPACE=os.environ.get("TEMPORAL_NAMESPACE", "infra-provisioning-queue")
TEMPORAL_INFRA_PROVISION_TASK_QUEUE=os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", "infra-provisioning-queue")


async def main():
	logging.basicConfig(level=logging.INFO)

	# Create client connected to server at the given address
	# TODO: take host as an arg / config item
	client = await Client.connect(TEMPORAL_HOST_URL)

	tf_directory = "./terraform"

	run_1 = TerraformRunDetails(
		# TODO: take a module name?
		# TODO: add additional parameters?
		directory=tf_directory
	)

	# Execute a workflow
	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		run_1,
		id=f"infra-provisioning-run-{uuid.uuid4()}",
		task_queue=PROVISION_INFRA_QUEUE_NAME,
		# TODO: add the directory as a custom attribute
	)

	print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")

	result = await handle.result()

	print(f"Result: {result}")


if __name__ == "__main__":
	asyncio.run(main())
