import pytest
import dataclasses
import json
from temporalio.client import WorkflowHistory
from temporalio.worker import Replayer
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import converter
from temporalio import activity
from workflows.apply import ProvisionInfraWorkflow
from shared.base import TerraformRunDetails, TEMPORAL_TASK_QUEUE
from shared.codec import EncryptionCodec

@pytest.mark.asyncio
async def test_successful_provision_replay():
	history = ""

	with open("tests/histories/happy_path_provision_events_encrypted.json", "r") as fh:
		history = fh.read()

	replayer = Replayer(
		workflows=[ProvisionInfraWorkflow],
		data_converter=dataclasses.replace(
			converter.default(),
			payload_codec=EncryptionCodec(),
			failure_converter_class=converter.DefaultFailureConverterWithEncodedAttributes
		)
	)

	workflow_id = json.loads(history)["events"][0]["workflowExecutionStartedEventAttributes"]["workflowId"]
	await replayer.replay_workflow(
		WorkflowHistory.from_json(workflow_id, history)
	)


@pytest.mark.asyncio
async def test_successful_provisioning():

	async with await WorkflowEnvironment.start_time_skipping() as env:
		mock_input = TerraformRunDetails(
			directory="terraform/minikube_kuard",
			include_custom_search_attrs=False, # NOTE: tests not working with custom search attrs
			hard_fail_policy=False,
			apply_timeout_secs=300,
			ephemeral=False,
		)

		async with Worker(
		env.client,
			task_queue=TEMPORAL_TASK_QUEUE,
			workflows=[ProvisionInfraWorkflow],
			activities=[
				terraform_init_mocked,
				terraform_plan_mocked,
				terraform_apply_mocked,
				terraform_destroy_mocked,
				terraform_output_mocked,
				policy_check_mocked,
			],
		):
			output = await env.client.execute_workflow(
				ProvisionInfraWorkflow.run,
				mock_input,
				id="test-provision-workflow-id",
				task_queue=TEMPORAL_TASK_QUEUE,
			)

			assert "mocked output details" in output["output"]

@activity.defn(name="terraform_init")
async def terraform_init_mocked(data: TerraformRunDetails) -> tuple:
    return "Terraform init succeeded", "<stderr>"

@activity.defn(name="terraform_plan")
async def terraform_plan_mocked(data: TerraformRunDetails) -> tuple:
    return "Terraform plan succeeded", "mocked plan JSON details"

@activity.defn(name="terraform_apply")
async def terraform_apply_mocked(data: TerraformRunDetails) -> str:
	return "Terraform apply succeeded"

@activity.defn(name="terraform_output")
async def terraform_output_mocked(data: TerraformRunDetails) -> dict:
	return {"output": "mocked output details"}

@activity.defn(name="policy_check")
async def policy_check_mocked(data: TerraformRunDetails) -> bool:
	return True

@activity.defn(name="terraform_destroy")
async def terraform_destroy_mocked(data: TerraformRunDetails) -> str:
	return "Terraform destroy succeeded"
