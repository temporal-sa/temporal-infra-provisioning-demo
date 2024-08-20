from pdb import run
import uuid
import os

from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, render_template, request, jsonify
from shared import get_temporal_client, TerraformRunDetails
from workflows import ProvisionInfraWorkflow
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")

app = Flask(__name__)

provision_status_key = SearchAttributeKey.for_text("provisionStatus")
tf_directory_key = SearchAttributeKey.for_text("tfDirectory")

"""
scenarios = [
	# TODO
	"HumanInLoopUpdate",
	"ChildWorkflow",
	"APIFailure",
	"RecoverableFailure",
]
"""

tf_runs = []

SCENARIOS = {
	"happy_path": {
		"description": "This deploys a namespace to Temporal Cloud with no issues.",
		"directory": "./terraform/happy_path"
	},
	"advanced_visibliity": {
		"description": "This deploys a namespace to Temporal Cloud with no issues, while publishing custom search attributes.",
		"directory": "./terraform/happy_path"
	},
	"human_in_the_loop": {
		"description": "This deploys an admin user to Temporal Cloud which requires an approval signal after a soft policy failure.",
		"directory": "./terraform/human_in_the_loop"
	},
	"non_recoverable": {
		"description": "This deploys an admin user to Temporal Cloud which will fail due to a hard soft policy failure.",
		"directory": "./terraform/human_in_the_loop"
	},
}


@app.route("/", methods=["GET", "POST"])
async def main():
	tf_run_id = f"provision-infra-{uuid.uuid4()}"
	return render_template(
		"index.html",
		tf_run_id=tf_run_id,
		scenarios=SCENARIOS
	)

@app.route("/provision_infra", methods=["GET", "POST"])
async def provision_infra():
	selected_scenario = request.args.get("scenario", "")
	tf_run_id = request.args.get("tf_run_id", "")
	tcloud_env_vars = { "TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY }
	tcloud_tf_dir = SCENARIOS[selected_scenario]["directory"]

	print(selected_scenario, selected_scenario == "non_recoverable")

	tf_run_details = TerraformRunDetails(
		id=tf_run_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars,
		hard_fail_policy=(selected_scenario == "non_recoverable")
	)

	client = await get_temporal_client()
	no_existing_workflow = False

	try:
		tf_workflow = client.get_workflow_handle(tf_run_id)
		await tf_workflow.describe()
	except Exception as e:
		no_existing_workflow = True

	if no_existing_workflow:
		await client.start_workflow(
			ProvisionInfraWorkflow.run,
			tf_run_details,
			id=tf_run_id,
			task_queue=TEMPORAL_TASK_QUEUE,
			search_attributes=TypedSearchAttributes([
				SearchAttributePair(provision_status_key, "uninitialized"),
				SearchAttributePair(tf_directory_key, tcloud_tf_dir)
			]),
		)
		tf_runs.append(tf_run_details)

	return render_template(
		"provisioning.html",
		tf_run_id=tf_run_id,
		selected_scenario=selected_scenario
	)


@app.route('/get_progress')
async def get_progress():
	tf_run_id = request.args.get('tf_run_id', "")
	payload = {
		"progress": 0,
		"status": "uninitialized",
		"plan": None
	}

	try:
		client = await get_temporal_client()
		tf_workflow = client.get_workflow_handle(tf_run_id)
		payload["status"] = await tf_workflow.query("get_current_status")
		payload["progress_percent"] = await tf_workflow.query("get_progress")
		payload["plan"] = await tf_workflow.query("get_plan")
		workflow_desc = await tf_workflow.describe()

		if workflow_desc.status == 3:
			error_message = "Workflow failed: {tf_run_id}"
			print(f"Error in get_progress route: {error_message}")
			return jsonify({"error": error_message}), 500

		return jsonify(payload)
	except Exception as e:
		print(e)
		return jsonify(payload)

@app.route('/provisioned')
async def provisioned():
	tf_run_id = request.args.get("tf_run_id", "")

	client = await get_temporal_client()
	tf_workflow = client.get_workflow_handle(tf_run_id)
	status = await tf_workflow.query("get_current_status")
	tf_workflow_output = await tf_workflow.result()

	return render_template(
		"provisioned.html",
		tf_run_id=tf_run_id,
		tf_workflow_output=tf_workflow_output,
		tf_run_status=status
	)

@app.route('/signal', methods=["POST"])
async def signal():
	tf_run_id = request.args.get("tf_run_id", "")
	decision = request.json.get("decision", False)
	reason = request.json.get("reason", "")

	try:
		client = await get_temporal_client()
		order_workflow = client.get_workflow_handle(tf_run_id)

		if decision is True:
			await order_workflow.signal("approve_apply", reason)
		else:
			await order_workflow.signal("deny_apply", reason)

	except Exception as e:
		print(f"Error sending signal: {str(e)}")
		return jsonify({"error": str(e)}), 500

	return "Signal received successfully", 200


if __name__ == "__main__":
	app.run(debug=True, port=3000)
