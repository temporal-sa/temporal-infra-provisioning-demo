from pdb import run
import uuid
import os

from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, render_template, request, jsonify
import temporal_client

TEMPORAL_CLOUD_API_KEY = os.environ.get("TEMPORAL_CLOUD_API_KEY", "")

# TODO: can I get this from the parent app?
@dataclass
class TerraformRunDetails:
	directory: str
	plan: str = ""
	env_vars: Dict[str, str] = field(default_factory=dict)
	apply_timeout_secs: int = 30

app = Flask(__name__)

scenarios = [
	"HappyPath",
	"AdvancedVisibility",
	"HumanInLoopSignal",
	# TODO
	# "HumanInLoopUpdate",
	# "ChildWorkflow",
	"APIFailure",
	"RecoverableFailure",
	"NonRecoverableFailure",
]

tf_runs = []

tf_modules = [
	{
		"name": "temporal_cloud",
		"description": "This deploys the Temporal Cloud infrastructure.",
		"directory": "./terraform"
	},
	{
		"name": "something_local",
		"description": "This deploys something locally to my machine.",
		"directory": "./terraform"
	}
]

client = temporal_client.get()

@app.route("/", methods=["GET", "POST"])
async def main():
	# TODO
	tf_run_id = str(uuid.uuid4().int)[:6]
	return render_template(
		"index.html",
		tf_modules=tf_modules,
		tf_run_id=tf_run_id,
		scenarios=scenarios
	)

@app.route("/provision_infra", methods=["GET", "POST"])
async def provision_infra():
	selected_scenario = request.args.get('scenario')
	tf_run_id = request.args.get('tf_run_id')
	tf_module_name = request.args.get('tf_module_name')
	tcloud_env_vars = { "TEMPORAL_CLOUD_API_KEY": TEMPORAL_CLOUD_API_KEY }
	tcloud_tf_dir = ""

	for module in tf_modules:
		if module["name"] == tf_module_name:
			tcloud_tf_dir = module["directory"]
			break

	run_details = TerraformRunDetails(
		directory=tcloud_tf_dir,
		env_vars=tcloud_env_vars
	)
	print(run_details)

	# TODO: add a run to the table

	"""
	input = OrderInput(
		OrderId= order_id,
		Address=shipping_data["address"],
	)

	await client.start_workflow(
		"OrderWorkflow"+selected_scenario,
		input,
		id=f'order-{order_id}',
		task_queue=os.getenv("TEMPORAL_TASK_QUEUE"),
	)
	"""


	return render_template(
		"index.html",
		tf_modules=tf_modules,
		tf_run_id=tf_run_id,
		scenarios=scenarios
	)

if __name__ == "__main__":
	app.run(debug=True, port=3000)
