import asyncio
import logging
import os

from temporalio.worker import Worker
from shared import get_temporal_client
from activities import ProvisioningActivities
from workflows import ProvisionInfraWorkflow

TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

async def main() -> None:
	logging.basicConfig(level=logging.INFO)

	client = await get_temporal_client()
	activities = ProvisioningActivities()

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
	await worker.run()


if __name__ == "__main__":
	asyncio.run(main())