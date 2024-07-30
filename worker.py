import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from activities import ProvisioningActivities
from shared import PROVISION_INFRA_QUEUE_NAME
from workflows import ProvisionInfraWorkflow


async def main() -> None:
	logging.basicConfig(level=logging.INFO)
	# TODO: take arguments in at runtime
	client: Client = await Client.connect("localhost:7233", namespace="default")
	# Run the worker
	activities = ProvisioningActivities()

	worker: Worker = Worker(
		client,
		task_queue=PROVISION_INFRA_QUEUE_NAME,
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