import asyncio
import uuid
import logging
import os
from workflows import ProvisionInfraWorkflow
from shared import TerraformRunDetails, get_temporal_client

from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get the TEMPORAL_HOST_URL environment variable, defaulting to "localhost:7233" if not set
TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")

# Get the TEMPORAL_MTLS_TLS_CERT environment variable, which stores the TLS certificate for mTLS authentication
TEMPORAL_MTLS_TLS_CERT = os.environ.get("TEMPORAL_MTLS_TLS_CERT", "")

# Get the TEMPORAL_MTLS_TLS_KEY environment variable, which stores the TLS key for mTLS authentication
TEMPORAL_MTLS_TLS_KEY = os.environ.get("TEMPORAL_MTLS_TLS_KEY", "")

# Get the TEMPORAL_NAMESPACE environment variable, defaulting to "default" if not set
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

# Get the TEMPORAL_TASK_QUEUE environment variable, defaulting to "provision-infra" if not set
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

# Get the TEMPORAL_CLOUD_API_KEY environment variable, which stores the API key for Temporal Cloud
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")

# Determine whether to encrypt payloads based on the ENCRYPT_PAYLOADS environment variable
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')


async def main():
	logging.basicConfig(level=logging.INFO)

	# Get the Temporal client
	client = await get_temporal_client()

	# Set the directory for the Terraform configuration files
	tcloud_tf_dir = "./terraform/tcloud_namespace"

	# Set the environment variables for Terraform
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY
	}

	# Generate a unique ID for the workflow
	wf_id = f"provision-infra-{uuid.uuid4()}"

	# Create the TerraformRunDetails object
	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars
	)

	# Define the search attributes for the workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")
	search_attributes = TypedSearchAttributes([
		SearchAttributePair(provision_status_key, "uninitialized"),
		SearchAttributePair(tf_directory_key, tcloud_tf_dir)
	])

	# Start the workflow
	handle = await client.start_workflow(
		ProvisionInfraWorkflow.run,
		tf_run_details,
		id=wf_id,
		task_queue=TEMPORAL_TASK_QUEUE,
		search_attributes=search_attributes,
	)

	# Wait for the workflow to complete and get the result
	result = await handle.result()

	# Print the result
	print(f"Result: {result}")


if __name__ == "__main__":
	# Run the main function
	asyncio.run(main())
