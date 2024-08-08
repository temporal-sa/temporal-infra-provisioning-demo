# temporal_infra_provisioning_demo

| Prerequisites      |    | Features       |    | Patterns            |    |
|:-------------------|----|----------------|----|---------------------|----|
| Network Connection | ✅ | Schedule       |    | Entity              |    |
| GitHub Access      |    | Local Activity | ✅ | Long-Running        | ✅ |
| Python 3.12        | ✅ | Timer          |    | Fanout              |    |
| Poetry 1.8.3       | ✅ | Signal         | ✅ | Continue As New     |    |
| Terraform 1.9.0    | ✅ | Query          | ✅ | Manual Intervention | ✅ |
| Open Policy Agent  |    | Heartbeat      | ✅ | Long-polling        |    |
|                    |    | Retry          | ✅ | Polyglot            |    |
|                    |    | Data Converter | ✅ |                     |    |
|                    |    | Codec Server   | ✅ |                     |    |
|                    |    | Custom Attrs   | ✅ |                     |    |
|                    |    | Worker Metrics |    |                     |    |

```bash
# authenticate your session
tcld login
# generate an API Key
tcld apikey create -n "terraform-test" --desc "Testing the API Key for the TF Provider" -d 90d
```

```bash
# replace <yoursecretkey> with the "secretKey": output from tcld apikey create command
export TEMPORAL_CLOUD_API_KEY=""
```

```bash
export TEMPORAL_HOST_URL="<namespace>.<accountId>.tmprl.cloud:7233"
export TEMPORAL_MTLS_TLS_CERT="/path/to/ca.pem"
export TEMPORAL_MTLS_TLS_KEY="/path/to/ca.key"
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_INFRA_PROVISION_TASK_QUEUE="infra-provisioning"
```

Before kicking off the starter, make sure the custom search attributes have been created.

```bash
temporal operator search-attribute create --namespace $TEMPORAL_NAMESPACE --name provisionStatus --type text
temporal operator search-attribute create --namespace $TEMPORAL_NAMESPACE --name tfDirectory --type text
```

Make sure the dependencies for Python have been installed via Poetry.

```bash
poetry install
```

Start the Codec server locally.

```bash
poetry run python codec_server.py --web http://localhost:8080
```

Then run the worker (be sure you have the environment variable set).

```bash
poetry run python worker.py
```

Once you start the worker, submit a workflow using the starter (also needs the environment varialbes set).

```bash
poetry run python starter.py
```

To query a workflow for it's current status, you can use the below command with the relevant in place of the current workflow ID.

```bash
temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="query_current_state"

temporal workflow query \
    --workflow-id="<WORKFLOW-ID>" \
    --type="query_signal_reason"
```

## Provision Workflow

### Provision Activities

- Terraform Init
- Terraform Plan
- Evaluate Policy
- Terraform Apply
- Terraform Show

### Provision Signals

- Human Approval of Policy Failure
- Human Denial of Policy Failure

### Provision Queries

- Get Progress

## TODO

- Clear TODOs, more comments all over, no prints, linting, final README
- ENCRYPT_PAYLOADS=true
- Slides on how to structure the demo.
- UI (Take from Order Management)
- For each scenario we created a different workflow so it’s easy to follow.
- Retry plans

## Ideas

- Ephemeral Infrastructure w/ keepalives on the TTL
- OPA (Check if a namespace is being deleted)
- SDK metrics / Grafana integration
- Public Module Registry
- Certs from Vault option
- Compensations?
- Destroy workflow
- GH actions
- Sticky Activities?

## Questions

- Terraform Cloud / OPA Server vs what I am doing
- Is this something we want to use for ephermeral scale testing environments?
- Do we want to make this save statefiles / planfiles across runs? Load them up? Is this valuable enough?

## Notes

- Setting the insecure flag in the TF config led to an irrecoverable HTTP/2 error.
