import asyncio
import sys

from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, PROVISION_INFRA_QUEUE_NAME
from temporalio.client import Client


async def main():
	# Create client connected to server at the given address
	# TODO: take host as an arg / config item
	client = await Client.connect("localhost:7233")

	run_1 = TerraformRunDetails(
		# TODO: take a module name?
		directory="terraform/"
	)

	# Execute a workflow
	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		run_1,
		id="infra-provisioning-run-1",
		task_queue=PROVISION_INFRA_QUEUE_NAME,
	)

	print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")

	result = await handle.result()

	print(f"Result: {result}")


if __name__ == "__main__":
	asyncio.run(main())
