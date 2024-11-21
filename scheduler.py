import asyncio
import uuid
import logging
import os
from datetime import timedelta
from workflows.destroy import DeprovisionInfraWorkflow
from shared.base import TerraformRunDetails, get_temporal_client, TEMPORAL_TASK_QUEUE

from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair
from temporalio.client import Schedule, ScheduleActionStartWorkflow, \
	ScheduleIntervalSpec, ScheduleSpec, ScheduleState

# Get the TF_VAR_prefix environment variable, defaulting to "temporal-sa" if not set
# NOTE: This is a specific env var for attribution for Terraform.
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

	# Generate unique IDs for the workflows
	wf_id_minikube_kuard = f"provision-minikube-kuard-{uuid.uuid4()}"

	# Create the TerraformRunDetails object for namespace
	tf_run_details_minikube_kuard = TerraformRunDetails(
		id=wf_id_minikube_kuard,
		directory=minikube_kuard_dir,
		env_vars=tcloud_env_vars,
		ephemeral=True
	)

	# Create the destroy schedule for minikube_kuard
	minikube_kuard_schedule_id = f"destroy-minikube-kuard-schedule-{uuid.uuid4()}"
	await client.create_schedule(
		minikube_kuard_schedule_id,
		Schedule(
			action=ScheduleActionStartWorkflow(
				DeprovisionInfraWorkflow.run,
				tf_run_details_minikube_kuard,
				id=f"scheduled-destroy-minikube-kuard-{uuid.uuid4()}",
				task_queue=TEMPORAL_TASK_QUEUE,
			),
			spec=ScheduleSpec(
				intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))]
			),
			state=ScheduleState(
				note="Destroy minikube kuard schedule.",
				limited_actions=True,
				remaining_actions=3  # Limit to 3 executions
			),
		),
	)

	print(f"Destroy schedule created with ID: {minikube_kuard_schedule_id}")

if __name__ == "__main__":
	# Run the main function
	asyncio.run(main())
