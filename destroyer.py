import asyncio
import uuid
import logging
import os
from workflows.destroy import DeprovisionInfraWorkflow
from shared.base import TerraformRunDetails, get_temporal_client

from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get the TEMPORAL_TASK_QUEUE environment variable, defaulting to "provision-infra" if not set
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

# Get the TEMPORAL_CLOUD_API_KEY environment variable, which stores the API key for Temporal Cloud
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")

# Get the TF_VAR_prefix environment variable, defaulting to "temporal-sa" if not set
# NOTE: This is a specific env var for mat for Terraform.
TF_VAR_prefix = os.environ.get("TF_VAR_prefix", "temporal-sa")

async def main():
	logging.basicConfig(level=logging.INFO)

	# Get the Temporal client
	client = await get_temporal_client()

	# Set the directory for the Terraform configuration files
	tcloud_tf_dir = "./terraform/tcloud_namespace"

	# Set the environment variables for Terraform
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY,
		"TF_VAR_prefix": TF_VAR_prefix
	}

	# Generate a unique ID for the workflow
	wf_id = f"deprovision-infra-{uuid.uuid4()}"

	# Create the TerraformRunDetails object
	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars,
	)

	# Define the search attributes for the workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")
	search_attributes = TypedSearchAttributes([
		SearchAttributePair(provision_status_key, ""),
		SearchAttributePair(tf_directory_key, tcloud_tf_dir)
	])

	# Start the workflow
	handle = await client.start_workflow(
		DeprovisionInfraWorkflow.run,
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
