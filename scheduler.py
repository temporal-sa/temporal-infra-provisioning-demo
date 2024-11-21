import asyncio
import uuid
import logging
import os
from datetime import timedelta
from workflows.destroy import DeprovisionInfraWorkflow
from shared.base import TerraformRunDetails, get_temporal_client, TEMPORAL_CLOUD_API_KEY, \
	TEMPORAL_TASK_QUEUE

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
	tcloud_tf_dir_namespace = "./terraform/tcloud_namespace"
	tcloud_tf_dir_admin_user = "./terraform/tcloud_admin_user"

	# Set the environment variables for Terraform
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY,
		"TF_VAR_prefix": TF_VAR_prefix
	}

	# Generate unique IDs for the workflows
	wf_id_namespace = f"provision-namespace-{uuid.uuid4()}"
	wf_id_admin_user = f"provision-admin-user-{uuid.uuid4()}"

	# Create the TerraformRunDetails object for namespace
	tf_run_details_namespace = TerraformRunDetails(
		id=wf_id_namespace,
		directory=tcloud_tf_dir_namespace,
		env_vars=tcloud_env_vars,
		ephemeral=True
	)

	# Create the TerraformRunDetails object for admin_user
	tf_run_details_admin_user = TerraformRunDetails(
		id=wf_id_admin_user,
		directory=tcloud_tf_dir_admin_user,
		env_vars=tcloud_env_vars,
		ephemeral=True
	)

	# Create the destroy schedule for admin_user
	admin_user_schedule_id = f"destroy-admin-user-schedule-{uuid.uuid4()}"
	await client.create_schedule(
		admin_user_schedule_id,
		Schedule(
			action=ScheduleActionStartWorkflow(
				DeprovisionInfraWorkflow.run,
				tf_run_details_admin_user,
				id=f"scheduled-destroy-admin-user-{uuid.uuid4()}",
				task_queue=TEMPORAL_TASK_QUEUE,
			),
			spec=ScheduleSpec(
				intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))]
			),
			state=ScheduleState(
				note="Destroy admin user schedule.",
				limited_actions=True,
				remaining_actions=3  # Limit to 3 executions
			),
		),
	)

	# Create the destroy schedule for namespace
	namespace_schedule_id = f"destroy-namespace-schedule-{uuid.uuid4()}"
	await client.create_schedule(
		namespace_schedule_id,
		Schedule(
			action=ScheduleActionStartWorkflow(
				DeprovisionInfraWorkflow.run,
				tf_run_details_namespace,
				id=f"scheduled-destroy-namespace-{uuid.uuid4()}",
				task_queue=TEMPORAL_TASK_QUEUE,
			),
			spec=ScheduleSpec(
				intervals=[ScheduleIntervalSpec(every=timedelta(minutes=30))]
			),
			state=ScheduleState(
				note="Destroy namespace schedule.",
				limited_actions=True,
				remaining_actions=3  # Limit to 3 executions
			),
		),
	)

	print(f"Destroy schedule created with ID: {admin_user_schedule_id}")
	print(f"Destroy schedule created with ID: {namespace_schedule_id}")

if __name__ == "__main__":
	# Run the main function
	asyncio.run(main())
