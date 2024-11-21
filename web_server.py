import uuid
import os
import re
from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, render_template, request, jsonify
from shared.base import get_temporal_client, TerraformRunDetails, ApplyDecisionDetails
from workflows.apply import ProvisionInfraWorkflow
from workflows.destroy import DeprovisionInfraWorkflow

from temporalio.exceptions import ApplicationError
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, \
	SearchAttributePair

# Get the Temporal host URL from the environment variable, default to "localhost:7233"
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
# Get the Temporal namespace from the environment variable, default to "default"
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
# Get the Temporal task queue from the environment variable, default to "provision-infra"
TEMPORAL_TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "provision-infra")
# Get the Temporal Cloud API key from the environment variable, default to an empty string
TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")
# Determine whether to encrypt payloads based on the environment variable, default to False
ENCRYPT_PAYLOADS = os.getenv("ENCRYPT_PAYLOADS", 'false').lower() in ('true', '1', 't')
# Get the TF_VAR_prefix environment variable, defaulting to "temporal-sa" if not set
# NOTE: This is a specific env var for mat for Terraform.
TF_VAR_prefix = os.environ.get("TF_VAR_prefix", "temporal-sa")

app = Flask(__name__)

# Define search attribute keys for workflow search
provision_status_key = SearchAttributeKey.for_text("provisionStatus")
tf_directory_key = SearchAttributeKey.for_text("tfDirectory")
scenario_key = SearchAttributeKey.for_text("scenario")
temporal_ui_url = TEMPORAL_ADDRESS.replace("7233", "8233") if "localhost" in TEMPORAL_ADDRESS \
	else "https://cloud.temporal.io"
tf_runs = []

# Define the available scenarios
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
		"title": "Human in the Loop (Update w/ Validation)",
		"description": "This deploys an admin user to Temporal Cloud which requires an approval update, including validation, after a soft policy failure.",
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
		"directory": "./terraform/tcloud_admin_user"
	},
	"api_failure": {
		"title": "API Failure (recover on 5th attempt)",
		"description": "This will get to the apply stage and then simulate an API failure, recovering after 5 attempts.",
		"directory": "./terraform/tcloud_namespace"
	},
	"ephemeral": {
		"title": "Ephemeral (Destroy After N seconds, with Durable Timers)",
		"description": "This will follow the Happy Path, but will tear down the infrastructure after a user defined number of seconds (default 15s), using durable timers.",
		"directory": "./terraform/tcloud_namespace"
	},
	"destroy": {
		"title": "Destroy",
		"description": "This will tear down the infrastructure immediately.",
		"directory": "./terraform/tcloud_namespace"
	},
}

def _safe_insert_tf_run(tf_run: dict):
	global tf_runs
	# Always insert the run as the first item in the list
	tf_runs.insert(0, tf_run) if tf_run["id"] not in [run["id"] for run in tf_runs] else None

def _scrub_sensitive_data(tf_workflow_output: dict):
	for key, value in tf_workflow_output.items():
		if value["sensitive"]:
			tf_workflow_output[key]["value"] = "<sensitive>"
	return tf_workflow_output

# Define the main route
@app.route("/", methods=["GET", "POST"])
async def main():
	# Generate a unique workflow ID
	wf_id = f"provision-infra-{uuid.uuid4()}"

	return render_template(
		"index.html",
		wf_id=wf_id,
		tf_runs=tf_runs,
		scenarios=SCENARIOS,
		temporal_host_url=TEMPORAL_ADDRESS,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

# Define the run_workflow route
@app.route("/run_workflow", methods=["GET", "POST"])
async def run_workflow():
	# Get the selected scenario and workflow ID from the request arguments
	selected_scenario = request.args.get("scenario", "")
	wf_id = request.args.get("wf_id", "")
	ephemeral_ttl = int(request.args.get("ephemeral_ttl", 15))

	# Set Temporal Cloud environment variables based on the selected scenario
	tcloud_env_vars = {
		"TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY,
		"TF_VAR_prefix": TF_VAR_prefix
	}

	tcloud_tf_dir = SCENARIOS[selected_scenario]["directory"]

	# Create Terraform run details
	tf_run_details = TerraformRunDetails(
		id=wf_id,
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars,
		# NOTE: Only hard fail the policy in the non-recoverable failure scenario
		hard_fail_policy=(selected_scenario == "non_recoverable_failure"),
		# NOTE: Only disable the custom search attributes on the happy path
		# so that we can demonstrate that visibility on the other scenarios.
		include_custom_search_attrs=(selected_scenario != "happy_path"),
		# NOTE: You can create a non-recoverable failure in the Plan stage instead of the the
		# Eval Policy stage if you uncomment the below.
		# env_vars=(tcloud_env_vars if selected_scenario != "non_recoverable_failure" else {} ),
		simulate_api_failure=(selected_scenario == "api_failure"),
		ephemeral=(selected_scenario == "ephemeral"),
		ephemeral_ttl=ephemeral_ttl,
	)

	# Get the Temporal client
	client = await get_temporal_client()
	no_existing_workflow = False

	try:
		# Check if the workflow already exists
		tf_workflow = client.get_workflow_handle(wf_id)
		await tf_workflow.describe()
	except Exception as e:
		no_existing_workflow = True

	if no_existing_workflow:
		if selected_scenario != "destroy":
			# Start the workflow if it doesn't exist
			await client.start_workflow(
				ProvisionInfraWorkflow.run,
				tf_run_details,
				id=wf_id,
				task_queue=TEMPORAL_TASK_QUEUE,
				search_attributes=TypedSearchAttributes([
					SearchAttributePair(provision_status_key, ""),
					SearchAttributePair(tf_directory_key, tcloud_tf_dir),
					SearchAttributePair(scenario_key, selected_scenario)
				]),
			)
		else:
			await client.start_workflow(
				DeprovisionInfraWorkflow.run,
				tf_run_details,
				id=wf_id,
				task_queue=TEMPORAL_TASK_QUEUE,
				search_attributes=TypedSearchAttributes([
					SearchAttributePair(provision_status_key, ""),
					SearchAttributePair(tf_directory_key, tcloud_tf_dir),
					SearchAttributePair(scenario_key, selected_scenario)
				]),
			)

	return render_template(
		"provisioning.html",
		wf_id=wf_id,
		tf_runs=tf_runs,
		selected_scenario=selected_scenario,
		temporal_host_url=TEMPORAL_ADDRESS,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

# Define the get_progress route
@app.route('/get_progress')
async def get_progress():
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

# Define the provisioned route
@app.route('/provisioned')
async def provisioned():
	wf_id = request.args.get("wf_id", "")
	scenario = request.args.get("scenario", "")

	client = await get_temporal_client()
	tf_workflow = client.get_workflow_handle(wf_id)
	status = await tf_workflow.query("get_current_status")
	tf_workflow_output = await tf_workflow.result()

	_safe_insert_tf_run({
		"id": wf_id,
		"scenario": scenario,
		"status": status,
	})

	tf_workflow_output = _scrub_sensitive_data(tf_workflow_output)

	return render_template(
		"provisioned.html",
		wf_id=wf_id,
		tf_runs=tf_runs,
		tf_workflow_output=tf_workflow_output,
		tf_run_status=status,
		temporal_host_url=TEMPORAL_ADDRESS,
		temporal_ui_url=temporal_ui_url,
		temporal_namespace=TEMPORAL_NAMESPACE,
		payloads_encrypted=ENCRYPT_PAYLOADS
	)

# Define the signal route
@app.route('/signal', methods=["POST"])
async def signal():
	wf_id = request.args.get("wf_id", "")
	signal_type = request.json.get("signalType", "")
	payload = request.json.get("payload", False)

	try:
		client = await get_temporal_client()
		order_workflow = client.get_workflow_handle(wf_id)

		if signal_type == "signal_apply_decision":
			apply_decision = ApplyDecisionDetails(
				is_approved=payload
			)
			await order_workflow.signal(signal_type, apply_decision)
		elif signal_type == "request_continue_as_new":
			await order_workflow.signal(signal_type)
		else:
			raise Exception("Signal type not supported")

	except Exception as e:
		print(f"Error sending signal: {str(e)}")
		return jsonify({"error": str(e)}), 500

	return "Signal received successfully", 200

# Define the update route
@app.route('/update', methods=["POST"])
async def update():
	wf_id = request.args.get("wf_id", "")
	decision = request.json.get("decision", False)
	reason = request.json.get("reason", "")

	try:
		client = await get_temporal_client()
		order_workflow = client.get_workflow_handle(wf_id)
		print(order_workflow)

		apply_decision = ApplyDecisionDetails(
			reason=reason,
			is_approved=decision
		)
		print(apply_decision)
		result = await order_workflow.execute_update("update_apply_decision", apply_decision)

		return jsonify({"result": result}), 200
	except Exception as e:
		print(f"Error sending update: {str(e)}")
		# return jsonify({"error": ""}), 500
		return jsonify({"result": "Error sending update. Make sure your reason is not empty."}), 422

# Run the Flask app
if __name__ == "__main__":
	app.run(debug=True, port=3000)
