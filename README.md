# Temporal Infrastructure Provisioning

| Prerequisites       |    | Features       |    | Patterns            |    |
|:--------------------|----|----------------|----|---------------------|----|
| Network Connection  | ✅ | SDK Metrics     | ✅ | Entity              | ✅ |
| Python 3.12         | ✅ | Timer           | ✅ | Long-polling        | ✅ |
| Poetry 1.8.3        | ✅ | Reset           | ✅ | Long-running        | ✅ |
| Terraform 1.9.0     | ✅ | Signal          | ✅ | Continue As New     | ✅ |
| Temporal Cloud Acct | ✅ | Query           | ✅ | Human in the Loop   | ✅ |
| Minikube 1.3.4      | ✅ | Heartbeat       | ✅ | Polyglot            |    |
|                     |    | Update          | ✅ |                     |    |
|                     |    | Retry           | ✅ |                     |    |
|                     |    | Data Converter  | ✅ |                     |    |
|                     |    | Codec Server    | ✅ |                     |    |
|                     |    | Custom Attrs    | ✅ |                     |    |
|                     |    | Replay Tests    | ✅ |                     |    |
|                     |    | Schedule        | ✅ |                     |    |
|                     |    | Local Activity  | ✅ |                     |    |
|                     |    | Nexus           |    |                     |    |

![Temporal Infrastructure Provisioning UI Screenshot](./static/ui.png)

This demo has the building blocks for you to execute any terraform code to completion, but is
focused on provisioning [kuard](https://github.com/kubernetes/kuard) (Kubernetes Up and Running
Demo App) into a [minikube cluster](https://minikube.sigs.k8s.io/docs/). Because of that,
you'll need to make sure you have minikube installed and running, as well as kubectl configured
to use the minikube context.

```bash
minikube start
```

There are two additional Terraform configurations in this repo, one for provisioning a namespace
in Temporal Cloud, and one for provisioning an admin user in Temporal Cloud.. The starter script
will default to provisioning into minikube, but you can easily swap to Temporal Cloud by
uncommenting the relevant lines. You will need to set the `TEMPORAL_CLOUD_API_KEY` environment
variable to match the API key for your Temporal Cloud account. The UI is fully minikube based.

## Provision Workflow

### Provision Activities

Each of these activities has a short sleep period associated with them, to simulate a longer running
`terraform plan` and `terraform apply`, as well as longer policy evaluation.

- Terraform Init
- Terraform Plan
- Evaluate Policy
  - Reset Workflow (Get a New Plan w/ Continue as New) [Optional]
- Terraform Apply (leverages Heartbeats)
- Terraform Destroy (leverages Heartbeats)
- Terraform Output

### Provision Signals

- Human Approval/Denial of Policy Failure
- Continue as New (Get a new TF Plan)

### Provision Updates

- Human Approval/Denial of Policy Failure

### Provision Queries

- Get Status
- Get Reason
- Get Plan
- Get Progress

## Scenarios

### Happy Path

This deploys a Kubernetes Demo App into a minikube cluster with no issues.

### Advanced Visibility

This deploys a Kubernetes Demo App into a minikube cluster with no issues, while publishing custom
search attributes.

### Human in the Loop (Signal)

This will attempt to deploy a Kubernetes Demo App into a minikube cluster, but will fail due to a
soft policy failure, requiring an approval signal.

### Human in the Loop (Update w/ Validation)

This will attempt to deploy a Kubernetes Demo App into a minikube cluster, but will fail due to a
soft policy failure, requiring an approval update, including validation.

### Recoverable Failure (Bug in Code)

This will attempt to deploy a Kubernetes Demo App into a minikube cluster, but will fail due to
uncommenting an exception in the terraform_plan activity and restarting the worker, then
re-commenting and restarting the worker.

### Non-Recoverable Failure (Hard Policy Failure)

This will attempt to deploy a Kubernetes Demo App into a minikube cluster, but will fail due to a
hard policy failure, or you can delete the environment variables and fail out w/ a
`non_retryable_error`.

### API Failure (Recover on 5th Attempt)

This will get to the apply stage and then simulate an API failure, recovering after 5 attempts.

### Ephemeral (Destroy Infra After TTL)

This will follow the Happy Path, but will tear down the infrastructure after a user defined number
of seconds (default 15s), using durable timers.

### Destroy

This will run a destroy workflow on the namespace that was created in the happy path.

## Running the Demo

### Installing Dependencies

Make sure you have [Terraform](https://www.terraform.io/) installed, as the runner shells out
from Python to execute the locally installed `terraform` binary.

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

Install poetry (if you haven't already), then install the Python dependencies for this project.

```bash
pipx install poetry
poetry install
```

### Configuring the Environment

By default, this demo will run against `localhost:7233` in the `default` namespace, on the
`provision-infra` task queue, with no TLS configured. All of this can be overriden with the below
environment variables. Be sure these environment variables are present in each environment you are executing
workers, starters, or the UI in.

```bash
export TEMPORAL_ADDRESS="<namespace>.<accountId>.tmprl.cloud:7233"
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_INFRA_PROVISION_TASK_QUEUE="infra-provisioning"
```

#### Using mTLS for Authentication

If you want to use mTLS for authentication, you'll need to set the `TEMPORAL_CERT_PATH` and
`TEMPORAL_KEY_PATH` environment variables to the paths of your TLS certificate and key.

```bash
export TEMPORAL_CERT_PATH="/path/to/ca.pem"
export TEMPORAL_KEY_PATH="/path/to/ca.key"
```

#### Using an API Key for Authentication

If you want, you can use an API key to authenticate to your namespace, you will need to set you
`TEMPORAL_CLOUD_API_KEY` environment variable, and have API key auth enabled for your namespace.

```bash
export TEMPORAL_CLOUD_API_KEY="<secretKey>"
```

#### Using Data Converters and a Codec Server

If you plan to use Data Converters and a Codec server, you'll need to update the `ENCRYPT_PAYLOADS`
env var as well.

```bash
export ENCRYPT_PAYLOADS="true"
```

#### Using a Prefix for Terraform

Lastly, to make sure that the namespaces and users that are generated from this demo can be
attributed to a specific individual, please use the following environment variable to denote your
name. _The Terraform configuration will not execute without this value._

```bash
export TF_VAR_prefix="neil"
```

You can also optionally set which region you want to create the namespace in.

```bash
export TF_VAR_region="aws-us-east-1"
```

### Running and Configuring the Temporal Dev Server (Option #1)

If you are using the Temporal Dev Server, start the server with the `frontend.enableUpdateWorkflowExecution` config
option set to `true`, which will allow us to perform updates to our workflows.

```bash
temporal server start-dev --db-filename temporal.sqlite --dynamic-config-value frontend.enableUpdateWorkflowExecution=true
```

Before kicking off the starter or using the UI, make sure the custom search attributes have been
created. If you are using the Temporal dev server, use the `operator search-attribute create`
command.

```bash
temporal operator search-attribute create --namespace "default" --name provisionStatus --type text
temporal operator search-attribute create --namespace "default" --name tfDirectory --type text
temporal operator search-attribute create --namespace "default" --name scenario --type text
```

### Configuring Temporal Cloud (Option #2)

If you are using Temporal Cloud, the command will look a bit different, using `tcld namespace search-attributes-add`.
If you are not already logged into Temporal Cloud with `tcld` run `tcld login`.

```bash
tcld namespace search-attributes add -n $TEMPORAL_NAMESPACE --sa "provisionStatus=Text" --sa "tfDirectory=Text" --sa "scenario=Text"
```

### Running the Workflow

Then run the worker (be sure you have the environment variables set).

```bash
poetry run python worker.py
```

Once you start the worker, submit a provision workflow using the starter (this also needs the
environment variables set).

```bash
poetry run python starter.py
```

Once you start the worker, submit a deprovision workflow using the cleanup (also needs the
environment variables set).

```bash
poetry run python cleanup.py
```

### Starting the UI

Once you have run your first starter and confirmed that you have wired up the server, worker, and
starter, it's time to to start up the UI. This is where the most time will be spent with the demo.

```bash
poetry run python web_server.py
```

### Running and Using the Local Codec Server

If you are running your workflows with `ENCRYPT_PAYLOADS=true`, you'll likely want to use the
provided codec server. To start the Codec server locally, use the below command. Note the `--web`
is the URL from which the codec server will allow incoming CORS requests.

```bash
cd shared/
poetry run python codec_server.py --web http://localhost:8233
```

In the Temporal UI, configure your Codec server to use `http://localhost:8081/encryption_codec` and
do not check any other boxes. If you intend to use the compression codec that is available in the
data converter, you can use `http://localhost:8081/compression_codec`.

### Using the SA Shared Codec Server

In the Temporal UI, configure your Codec server to use `https://codec.tmprl-demo.cloud` and check
the "pass the user access token" box.

### Interacting with the Workflows

If you introduce a Terraform stanza that provisions a user with admin permissions, this workflow
will pause and wait for a signal or update to approve or deny the execution of the plan. If going
down the signal path, you don't need to provide a reason, but if you go down the update path, you
need to provide a reason for approval.

#### Signaling a Workflow

Signals are asynchronous, and do not require a message with the decision.

```bash
temporal workflow signal \
    --workflow-id="<workflow-id>" \
    --name update_apply_decision \
    --decision '{"is_approved": false"}'

temporal workflow signal \
    --workflow-id="<workflow-id>" \
    --name request_continue_as_new
```

#### Updating a Workflow

Updates are synchronous, and require a message with the decision to be accepted.

```bash
temporal workflow update \
    --workflow-id="<workflow-id>" \
    --name update_apply_decision \
    --decision '{"is_approved": true, "reason": "Approved after review"}'
```

#### Querying a Workflow

To query a workflow for it's current status, the plan, the signal reason or the progress, you can
use the below commands with the relevant in place of the current workflow ID.

```bash
temporal workflow query \
    --workflow-id="<workflow-id>" \
    --type="get_current_status"

temporal workflow query \
    --workflow-id="<workflow-id>" \
    --type="get_progress"

temporal workflow query \
    --workflow-id="<workflow-id>" \
    --type="get_plan"

temporal workflow query \
    --workflow-id="<workflow-id>" \
    --type="get_reason"
```

If you want to inspect the workflow more closely from the CLI, and you have `ENCRYPT_PAYLOADS=true`,
you can decrypt the payload with a command like the following.

```bash
temporal workflow show \
   --workflow-id <workflow-id> \
   --codec-endpoint 'http://localhost:8081/default'
```

#### Resetting a Workflow

There may be a scenario in which an approval takes so long to come in that the state of the
infrastructure may have drifted, meaning Terraform's plan is no longer valid. In that case, you
can reset the workflow execution to the plan stage, and get a new plan and policy check.

```bash
temporal workflow reset \
    --workflow-id="<workflow-id>" \
    --event-id="<event-id>"
```

### Using SDK Metrics

The worker will have SDK metrics for Prometheus enabled by default. To start up Prometheus and
Grafana quickly for a demo, follow the below.

```bash
cd metrics/
docker-compose up
```

When you connect to your Prometheus from Grafana, use the URL `http://prometheus:9090`. There is
an example dashboard to leverage in `metrics/dashboards/sdk-general.json`.

### Scheduling Destroy Workflows

There may be a scenario in which you want to schedule the destruction of the infrastructure. To
do so, run the `scheduler.py` file, which will destroy all of the infrastructure created by this demo
after a user defined interval (default is 5 minutes). It will run 3 times by default, so after
15 minutes you will need to manually clean up.

```bash
poetry run python scheduler.py
```

### Running the Tests

There are unit and replay tests for the provision and destroy workflows. To run the unit tests, use
the following command.

```bash
poetry run python -m pytest
```

### Cleaning Up

This demo provisions into your minikube cluster, so to keep things tidy and make sure you don't have
any lingering resources, you should clean up after yourself.

#### Using the UI

Select the "Destroy" scenario in the UI and click "Run". This will teardown the namespace that is
created, but not the user.

#### Using `cleanup.py`

The cleanup will start two destroy workflows, one for the namespace and one for the user.
Be sure the environment variables are set.

```bash
poetry run python cleanup.py
```

#### Using `terraform` Directly

To do so, make sure that you have your `TEMPORAL_CLOUD_API_KEY` env var set, then run the following.
You will have to move around the directories depending on what you need to `destroy`.

**DO NOT DELETE THEM IN THE UI - THIS WILL CAUSE YOUR TERRAFORM STATE TO DRIFT!**

```bash
cd terraform/minikube_kuard/
terraform destroy -auto-approve
```

---

## Experimental

### Minikube Demo

#### Prerequisites

- Minikube installed and running (`minikube start`)
- kubectl configured to use minikube context

#### Deploying Kubernetes Demo App (`kuard`)

The `terraform/minikube_kuard` directory contains configuration to deploy the Kubernetes Up and Running Demo (`kuard`) application to your local Minikube cluster.

```bash
cd terraform/minikube_kuard
terraform init
terraform apply
```

After applying, you can access the Kubernetes Demo App using the URL provided in the terraform output. You can also use:

```bash
minikube service kuard -n kuard-namespace
```

This will automatically open your browser to the correct URL and port.

### Docker

To run the worker in a container, build the image with:

```bash
docker build -t temporal-infra-worker .
docker build -t eklhad/temporal-infra-worker:0.0.1 .
docker tag eklhad/temporal-infra-worker:0.0.1 eklhad/temporal-infra-worker:0.0.1
docker tag eklhad/temporal-infra-worker:0.0.1 eklhad/temporal-infra-worker:latest
docker push eklhad/temporal-infra-worker:0.0.1
docker push eklhad/temporal-infra-worker:latest
```

And then run the container with:

```bash
# for local devlopment

docker run \
  --network="host"  \
  -e TEMPORAL_ADDRESS=$TEMPORAL_ADDRESS \
  -e TEMPORAL_NAMESPACE=$TEMPORAL_NAMESPACE \
  -e TEMPORAL_TASK_QUEUE=$TEMPORAL_TASK_QUEUE \
  -e TEMPORAL_CLOUD_API_KEY=$TEMPORAL_CLOUD_API_KEY \
  -e TF_VAR_prefix=$TF_VAR_prefix \
  -e ENCRYPT_PAYLOADS=$ENCRYPT_PAYLOADS \
  eklhad/temporal-infra-worker:latest

# for Temporal Cloud
docker run \
  --network="host" \
  -e TEMPORAL_ADDRESS=$TEMPORAL_ADDRESS \
  -e TEMPORAL_NAMESPACE=$TEMPORAL_NAMESPACE \
  -e TEMPORAL_TASK_QUEUE=$TEMPORAL_TASK_QUEUE \
  -e TEMPORAL_CLOUD_API_KEY=$TEMPORAL_CLOUD_API_KEY \
  -e TF_VAR_prefix=$TF_VAR_prefix \
  -e ENCRYPT_PAYLOADS=$ENCRYPT_PAYLOADS \
  -e TEMPORAL_CERT_PATH=/app/certs/client.pem \
  -e TEMPORAL_KEY_PATH=/app/certs/client.key \
  -v $TEMPORAL_MTLS_DIR:/app/certs \
  eklhad/temporal-infra-worker:latest
```

Note that with Docker Desktop, you'll need to use `host.docker.internal` instead of `localhost` to
access the host machine from within the container.
