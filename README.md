# Temporal Infrastructure Provisioning

_Leveraging the Temporal Python SDK and Terraform_

| Prerequisites      |    | Features       |    | Patterns            |    |
|:-------------------|----|----------------|----|---------------------|----|
| Network Connection | ✅ | Schedule       |    | Entity              |    |
| GitHub Actions     |    | Local Activity | ✅ | Long-Running        | ✅ |
| Python 3.12        | ✅ | Timer          |    | Fanout              |    |
| Poetry 1.8.3       | ✅ | Signal         | ✅ | Continue As New     |    |
| Terraform 1.9.0    | ✅ | Query          | ✅ | Manual Intervention | ✅ |
| Open Policy Agent  |    | Heartbeat      | ✅ | Long-polling        |    |
|                    |    | Update         |    | Polyglot            |    |
|                    |    | Retry          | ✅ |                     |    |
|                    |    | Data Converter | ✅ |                     |    |
|                    |    | Codec Server   | ✅ |                     |    |
|                    |    | Custom Attrs   | ✅ |                     |    |
|                    |    | Worker Metrics |    |                     |    |
|                    |    | Side Effect    |    |                     |    |

This demo has the building blocks for you to execute any terraform code to completion, but is focused on
provisioning namespaces and users in Temporal Cloud. Because of that, you will need to generate a
Temporal Cloud API key for usage with the Terraform plan. This is also a sensitive value and will
be published to whatever Temporal server you connect to, so it is recommended to leverage the
`ENCRYPT_PAYLOADS` variable, or that you retire the credential you use in the demo immediately.

## Provision Workflow

### Provision Activities

- Terraform Init
- Terraform Plan
- Evaluate Policy
- Terraform Apply
- Terraform Output

### Provision Signals

- Human Approval of Policy Failure
- Human Denial of Policy Failure

### Provision Updates

- Human Approval of Policy Failure
- Human Denial of Policy Failure

### Provision Queries

- Get Status
- Get Signal REason
- Get Plan
- Get Progress

## Running the Demo

To generate an API key, use `tcld`:

```bash
# authenticate your session
tcld login

# generate an API Key
tcld apikey create -n "terraform-test" --desc "Testing the API Key for the TF Provider" -d 90d
```

Then update your environment variables.

```bash
export TEMPORAL_CLOUD_API_KEY="<secretKey>"
export TEMPORAL_HOST_URL="<namespace>.<accountId>.tmprl.cloud:7233"
export TEMPORAL_MTLS_TLS_CERT="/path/to/ca.pem"
export TEMPORAL_MTLS_TLS_KEY="/path/to/ca.key"
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_INFRA_PROVISION_TASK_QUEUE="infra-provisioning"
export ENCRYPT_PAYLOADS="true"
```

Before kicking off the starter, make sure the custom search attributes have been created.

```bash
temporal server start-dev --ui-port 8080 --db-filename temporal.sqlite --dynamic-config-value frontend.enableUpdateWorkflowExecution=true
temporal operator search-attribute create --namespace $TEMPORAL_NAMESPACE --name provisionStatus --type text
temporal operator search-attribute create --namespace $TEMPORAL_NAMESPACE --name tfDirectory --type text
```

Make sure the dependencies for Python have been installed via Poetry.

```bash
poetry install
```

Start the Codec server locally.

```bash
poetry run python codec_server.py --web http://localhost:8081

temporal workflow show \
   --workflow-id <workflow-id>
   --codec-endpoint 'http://localhost:8081/default'
```

Then run the worker (be sure you have the environment variables set).

```bash
poetry run python worker.py
```

Once you start the worker, submit a workflow using the starter (also needs the environment variables set).

```bash
poetry run python starter.py
```

If you introduce a Terraform stanza that provisions a user with admin permissions, this workflow will pause and wait
for a signal to approve or deny the execution of the plan.

```bash
temporal workflow signal \
    --workflow-id="<WORKFLOW-ID>" \
    --name approve_apply \
    --reason "approving apply"

temporal workflow signal \
    --workflow-id="<WORKFLOW-ID>" \
    --name deny_apply \
    --reason "approving apply"
```

To query a workflow for it's current status, the plan, the signal reason or the progress, you can use the below commands with the relevant in place of the current workflow ID.

```bash
temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="get_current_status"

temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="get_progress"

temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="get_plan"

temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="get_signal_reason"
```

## Scenarios

### Happy Path

This deploys a namespace to Temporal Cloud with no issues.

### Advanced Visibility

This deploys a namespace to Temporal Cloud with no issues, while publishing custom search attributes.

### Human in the Loop Signal

This deploys an admin user to Temporal Cloud which requires an approval signal after a soft policy failure.

### Human in the Loop Update

This deploys an admin user to Temporal Cloud which requires an approval update after a soft policy failure.

### Recoverable Failure

This deploys an admin user to Temporal Cloud which will fail due to a divide by zero error, which can be commented out.

### Non-Recoverable Failure

This deploys an admin user to Temporal Cloud which will fail due to a hard policy failure.
