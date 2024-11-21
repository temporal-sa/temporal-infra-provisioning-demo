import asyncio
import uuid
import logging
import os
from workflows.destroy import DeprovisionInfraWorkflow
from shared.base import TerraformRunDetails, get_temporal_client, TEMPORAL_TASK_QUEUE

from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get the TF_VAR_prefix environment variable, defaulting to "temporal-sa" if not set
# NOTE: This is a specific env var for mat for Terraform.
TF_VAR_prefix = os.environ.get("TF_VAR_prefix", "temporal-sa")

async def main():
	logging.basicConfig(level=logging.INFO)

	# Get the Temporal client
	client = await get_temporal_client()

	# Set the directories for the Terraform configuration files
	minikube_kuard_dir = "./terraform/minikube_kuard"

	# Set the environment variables for Terraform
	tcloud_env_vars = {
		"TF_VAR_prefix": TF_VAR_prefix
	}

	# Generate unique IDs for the workflow
	namespace_wf_id = f"deprovision-infra-{uuid.uuid4()}"
	user_wf_id = f"deprovision-infra-{uuid.uuid4()}"

	# Create the TerraformRunDetails object
	tf_namespace_run_details = TerraformRunDetails(
		id=namespace_wf_id,
		env_vars=tcloud_env_vars,
		directory=minikube_kuard_dir
	)

	# Define the search attributes for the workflow
	provision_status_key = SearchAttributeKey.for_text("provisionStatus")
	tf_directory_key = SearchAttributeKey.for_text("tfDirectory")

	handle = await client.start_workflow(
		DeprovisionInfraWorkflow.run,
		tf_namespace_run_details,
		id=namespace_wf_id,
		task_queue=TEMPORAL_TASK_QUEUE,
		search_attributes=TypedSearchAttributes([
			SearchAttributePair(provision_status_key, ""),
			SearchAttributePair(tf_directory_key, minikube_kuard_dir)
		])
	)

	result = await handle.result()

	# Print the result
	print(f"Result: {result}")


if __name__ == "__main__":
	# Run the main function
	asyncio.run(main())
