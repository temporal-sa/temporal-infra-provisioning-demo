import asyncio
import logging
import os
from temporalio.worker import Worker
from shared.activities import ProvisioningActivities
from workflows.apply import ProvisionInfraWorkflow
from workflows.destroy import DeprovisionInfraWorkflow
from temporalio.client import Client
from shared.base import TEMPORAL_HOST_URL, TEMPORAL_NAMESPACE, TEMPORAL_CLOUD_API_KEY

# Get the task queue name from the environment variable, defaulting to "provision-infra"
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

async def update_api_key(client: Client) -> None:
	while True:
		updated_api_key = await fetch_updated_api_key()

		if updated_api_key != client.api_key:
			client.api_key = updated_api_key
			print("API Key updated:", client.api_key[:5] + "...")

		await asyncio.sleep(10)

async def fetch_updated_api_key() -> str:

	print("Fetching updated API key")
	return TEMPORAL_CLOUD_API_KEY

async def main() -> None:
	logging.basicConfig(level=logging.INFO)

	activities = ProvisioningActivities()

	client: Client = await Client.connect(
		TEMPORAL_HOST_URL,
		namespace=TEMPORAL_NAMESPACE,
		rpc_metadata={"temporal-namespace": TEMPORAL_NAMESPACE},
		api_key=TEMPORAL_CLOUD_API_KEY,
		tls=True
	)

	worker: Worker = Worker(
		client,
		task_queue=TEMPORAL_TASK_QUEUE,
		workflows=[ProvisionInfraWorkflow, DeprovisionInfraWorkflow],
		activities=[
			activities.terraform_init,
			activities.terraform_plan,
			activities.terraform_apply,
			activities.terraform_destroy,
			activities.terraform_output,
			activities.policy_check,
		]
	)

	print("FIRST KEY", client.api_key[:5] + "...")

	print("Starting worker and API key updater concurrently")
	await asyncio.gather(
		worker.run(),
		update_api_key(client)
	)


if __name__ == "__main__":
	# Run the main function using asyncio
	asyncio.run(main())
