import asyncio
import uuid
import logging
import os
from workflows.apply import ProvisionInfraWorkflow
from shared.base import TEMPORAL_CLOUD_API_KEY, TerraformRunDetails, get_temporal_client, TEMPORAL_TASK_QUEUE

from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get the TF_VAR_prefix environment variable, defaulting to "temporal-sa" if not set
# NOTE: This is a specific env var for attribution for Terraform.
TF_VAR_prefix = os.environ.get("TF_VAR_prefix", "temporal-sa")

async def main():
	logging.basicConfig(level=logging.INFO)

	# Get the Temporal client
	client = await get_temporal_client()

	# Set the directory for the Terraform configuration files
	minikube_kuard_dir = "./terraform/minikube_kuard"
	# NOTE: Uncomment this if you want to deploy to Temporal Cloud
	# tcloud_namespace_dir = "./terraform/tcloud_namespace"

	# Set the environment variables for Terraform
	tcloud_env_vars = {
		"TF_VAR_prefix": TF_VAR_prefix,
		# NOTE: Uncomment this if you want to deploy to Temporal Cloud
		# "TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY
	}

	# Generate a unique ID for the workflow
	wf_id = f"provision-infra-{uuid.uuid4()}"

	# Create the TerraformRunDetails object
	ephemeral = True
	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=minikube_kuard_dir,
		env_vars=tcloud_env_vars,
		ephemeral=ephemeral
	)

	if ephemeral:
		print("This TF run is ephemeral, so it will be deleted after a short delay.")

	# Define the search attributes for the workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")
	search_attributes = TypedSearchAttributes([
		SearchAttributePair(provision_status_key, ""),
		SearchAttributePair(tf_directory_key, minikube_kuard_dir)
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
