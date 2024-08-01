import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

from shared import PROVISION_INFRA_QUEUE_NAME
from activities import ProvisioningActivities
from workflows import ProvisionInfraWorkflow

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", None)
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", None)
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_INFRA_PROVISION_TASK_QUEUE = os.environ.get("TEMPORAL_INFRA_PROVISION_TASK_QUEUE", PROVISION_INFRA_QUEUE_NAME)
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")

async def main() -> None:
	logging.basicConfig(level=logging.INFO)
	# TODO: use the TLS stuff here.
	client: Client = await Client.connect(TEMPORAL_HOST_URL, namespace=TEMPORAL_NAMESPACE)
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