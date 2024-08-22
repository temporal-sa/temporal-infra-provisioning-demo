"""
This file contains a Flask web server that provides endpoints for provisioning infrastructure using Temporal workflows.

Endpoints:
- `/`: Renders the main page with options to select a provisioning scenario.
- `/provision_infra`: Initiates the infrastructure provisioning workflow based on the selected scenario.
- `/get_progress`: Retrieves the progress and status of the infrastructure provisioning workflow.
- `/provisioned`: Renders the page indicating that the infrastructure provisioning is complete.
- `/signal`: Handles the approval or denial signal for the human-in-the-loop scenario.
- `/update`: Handles the approval or denial update for the human-in-the-loop scenario.
"""

import uuid
import os
import re
from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, render_template, request, jsonify
from shared import get_temporal_client, TerraformRunDetails
from workflows import ProvisionInfraWorkflow
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get environment variables
TEMPORAL_HOST_URL = os.environ.get("TEMPORAL_HOST_URL", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')

# Create Flask app
app = Flask(__name__)

# Define search attribute keys
provision_status_key = SearchAttributeKey.for_text("provisionStatus")
tf_directory_key = SearchAttributeKey.for_text("tfDirectory")

# Initialize list to store Terraform run details
tf_runs = []

# Generate Temporal UI URL
temporal_ui_url = re.sub(r':\d+', ':8080', TEMPORAL_HOST_URL)

# Define provisioning scenarios
SCENARIOS = {
	"happy_path": {
		"title": "Happy Path",
		"description": "This deploys a namespace to Temporal Cloud with no issues.",
		"directory": "./terraform/tcloud_namespace"
	},
	"advanced_visibliity": {
		"title": "Advanced Visibility",
		"description": "This deploys a namespace to Temporal Cloud with no issues, while publishing custom search attributes.",
		"directory": "./terraform/tcloud_namespace"
	},
	"human_in_the_loop_signal": {
		"title": "Human in the Loop (Signal)",
		"description": "This deploys an admin user to Temporal Cloud which requires an approval signal after a soft policy failure.",
		"directory": "./terraform/tcloud_admin_user"
	},
	"human_in_the_loop_update": {
		"title": "Human in the Loop (Update)",
		"description": "This deploys an admin user to Temporal Cloud which requires an approval update after a soft policy failure.",
		"directory": "./terraform/tcloud_admin_user"
	},
	"recoverable_failure": {
		"title": "Recoverable Failure (Bug in Code)",
		"description": "This deploys an admin user to Temporal Cloud which will fail due to uncommenting an exception in the terraform_plan activity and restarting the worker, then recommenting and restarting the worker.",
		"directory": "./terraform/tcloud_namespace"
	},
	"non_recoverable_failure": {
		"title": "Non Recoverable Failure (Hard Policy Fail)",
		"description": "This can deploy an admin user to Temporal Cloud which will fail due to a hard policy failure, or can delete the environment variables and fail out w/ a non-retryable error.",
		"directory": "./terraform/tcloud_namespace"
	},
	"api_failure": {
		"title": "API Failure (recover on 3rd attempt)",
		"description": "This will get to the plan stage and then simulate an API failure, recovering after 3 attempts.",
		"directory": "./terraform/tcloud_namespace"
	},
}

@app.route("/", methods=["GET", "POST"])
async def main():
	"""
	Renders the main page with options to select a provisioning scenario.
	"""
	wf_id = f"provision-infra-{uuid.uuid4()}"

	return render_template(
		"index.html",
		wf_id=wf_id,
		tf_runs=tf_runs,
		scenarios=SCENARIOS,
		temporal_host_url=TEMPORAL_HOST_URL,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

@app.route("/provision_infra", methods=["GET", "POST"])
async def provision_infra():
	"""
	Initiates the infrastructure provisioning workflow based on the selected scenario.
	"""
	selected_scenario = request.args.get("scenario", "")
	wf_id = request.args.get("wf_id", "")

	tcloud_env_vars = { "TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY } \
		if selected_scenario != "non_recoverable_failure" else {}

	tcloud_tf_dir = SCENARIOS[selected_scenario]["directory"]

	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars,
		simulate_api_failure=(selected_scenario == "api_failure")
	)

	client = await get_temporal_client()
	no_existing_workflow = False

	try:
		tf_workflow = client.get_workflow_handle(wf_id)
		await tf_workflow.describe()
	except Exception as e:
		no_existing_workflow = True

	if no_existing_workflow:
		await client.start_workflow(
			ProvisionInfraWorkflow.run,
			tf_run_details,
			id=wf_id,
			task_queue=TEMPORAL_TASK_QUEUE,
			search_attributes=TypedSearchAttributes([
				SearchAttributePair(provision_status_key, "uninitialized"),
				SearchAttributePair(tf_directory_key, tcloud_tf_dir)
			]),
		)

	return render_template(
		"provisioning.html",
		wf_id=wf_id,
		selected_scenario=selected_scenario,
		temporal_host_url=TEMPORAL_HOST_URL,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

@app.route('/get_progress')
async def get_progress():
	"""
	Retrieves the progress and status of the infrastructure provisioning workflow.
	"""
	wf_id = request.args.get('wf_id', "")
	payload = {
		"progress": 0,
		"status": "uninitialized",
		"plan": None
	}

	try:
		client = await get_temporal_client()
		tf_workflow = client.get_workflow_handle(wf_id)
		payload["status"] = await tf_workflow.query("get_current_status")
		payload["progress_percent"] = await tf_workflow.query("get_progress")
		payload["plan"] = await tf_workflow.query("get_plan")
		workflow_desc = await tf_workflow.describe()

		if workflow_desc.status == 3:
			error_message = "Workflow failed: {wf_id}"
			print(f"Error in get_progress route: {error_message}")
			return jsonify({"error": error_message}), 500

		return jsonify(payload)
	except Exception as e:
		print(e)
		return jsonify(payload)

@app.route('/provisioned')
async def provisioned():
	"""
	Renders the page indicating that the infrastructure provisioning is complete.
	"""
	wf_id = request.args.get("wf_id", "")

	client = await get_temporal_client()
	tf_workflow = client.get_workflow_handle(wf_id)
	status = await tf_workflow.query("get_current_status")
	tf_workflow_output = await tf_workflow.result()

	# TODO: check for dupes before inserting
	tf_runs.insert(0, {
		"id": wf_id,
		"status": status,
	})

	# TODO: scrub sensitive in the server

	return render_template(
		"provisioned.html",
		wf_id=wf_id,
		tf_workflow_output=tf_workflow_output,
		tf_run_status=status,
		temporal_host_url=TEMPORAL_HOST_URL,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

@app.route('/signal', methods=["POST"])
async def signal():
	"""
	Handles the approval or denial signal for the human-in-the-loop scenario.
	"""
	wf_id = request.args.get("wf_id", "")
	decision = request.json.get("decision", False)
	reason = request.json.get("reason", "")

	try:
		client = await get_temporal_client()
		order_workflow = client.get_workflow_handle(wf_id)

		if decision is True:
			await order_workflow.signal("signal_approve_apply", reason)
		else:
			await order_workflow.signal("signal_deny_apply", reason)

	except Exception as e:
		print(f"Error sending signal: {str(e)}")
		return jsonify({"error": str(e)}), 500

	return "Signal received successfully", 200

@app.route('/update', methods=["POST"])
async def update():
	"""
	Handles the approval or denial update for the human-in-the-loop scenario.
	"""
	wf_id = request.args.get("wf_id", "")
	decision = request.json.get("decision", False)
	reason = request.json.get("reason", "")

	try:
		client = await get_temporal_client()
		order_workflow = client.get_workflow_handle(wf_id)

		if decision is True:
			await order_workflow.execute_update("update_approve_apply", reason)
		else:
			await order_workflow.execute_update("update_deny_apply", reason)

	except Exception as e:
		print(f"Error sending update: {str(e)}")
		return jsonify({"error": str(e)}), 500

	return "Update received successfully", 200

if __name__ == "__main__":
	app.run(debug=True, port=3000)
