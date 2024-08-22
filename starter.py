import asyncio
import uuid
import logging
import os

from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, get_temporal_client
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')


async def main():
	logging.basicConfig(level=logging.INFO)

	client = await get_temporal_client()
	tcloud_tf_dir = "./terraform/tcloud_namespace"
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY
	}

	wf_id = f"provision-infra-{uuid.uuid4()}"
	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars
	)

	# Execute a workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")

	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		tf_run_details,
		id=wf_id,
		task_queue=TEMPORAL_TASK_QUEUE,
		search_attributes=TypedSearchAttributes([
			SearchAttributePair(provision_status_key, "uninitialized"),
			SearchAttributePair(tf_directory_key, tcloud_tf_dir)
		]),
	)

	result = await handle.result()

	print(f"Result: {result}")


if __name__ == "__main__":
	asyncio.run(main())
