import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

from activities import ProvisioningActivities
from workflows import ProvisionInfraWorkflow

TEMPORAL_INFRA_PROVISION_TASK_QUEUE=os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", "infra-provisioning-queue")

async def main() -> None:
	logging.basicConfig(level=logging.INFO)
	# TODO: take arguments in at runtime
	client: Client = await Client.connect("localhost:7233", namespace="default")
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