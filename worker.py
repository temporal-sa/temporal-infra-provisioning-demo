import asyncio
import logging
import os
from temporalio.worker import Worker
from shared import get_temporal_client
from activities import ProvisioningActivities
from workflows import ProvisionInfraWorkflow

# Get the task queue name from the environment variable, defaulting to "provision-infra"
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

async def main() -> None:
	logging.basicConfig(level=logging.INFO)

	# Get the Temporal client
	client = await get_temporal_client()

	# Create an instance of the ProvisioningActivities class
	activities = ProvisioningActivities()

	# Create a worker instance
	worker: Worker = Worker(
		client,
		task_queue=TEMPORAL_TASK_QUEUE,
		workflows=[ProvisionInfraWorkflow],
		activities=[
			activities.terraform_init,
			activities.terraform_plan,
			activities.terraform_apply,
			activities.terraform_output,
			activities.policy_check,
		]
	)

	# Run the worker
	await worker.run()


if __name__ == "__main__":
	# Run the main function using asyncio
	asyncio.run(main())
