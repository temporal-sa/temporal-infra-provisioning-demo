# temporal_infra_provisioning_demo

| Prerequisites      |   | Features       |    | Patterns             |   |
|:-------------------|---|----------------|----|----------------------|---|
| Network Connection |   | Schedule       |    | Entity               |   |
|                    |   | Local Activity | ✅ | Long-Running        | ✅ |
| Python 3.12        | ✅ | Timer         |    | Fanout              |   |
| Poetry 1.8.3       | ✅ | Signal        | ✅ | Continue As New     |   |
| Terraform          |   | Query          | ✅ | Manual Intervention | ✅ |
| Open Policy Agent  |   | Heartbeat      |    | Long-polling        |   |
| GitHub Access      |   | Retry          | ✅ |                     |   |
|                    |   | Data Converter |    |                     |   |
|                    |   | Codec Server   |    |                     |   |
|                    |   | Polyglot       |    |                     |   |
|                    |   | Worker Metrics |    |                     |   |

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
export TEMPORAL_WORKER_METRICS_PORT=9090
export TEMPORAL_INFRA_PROVISION_TASK_QUEUE="infra-provisioning-python"
```

```bash
poetry install
poetry run python worker.py
poetry run python stater.py
```

## Provision Workflow

### Provision Activities

- Load State for Account
- Terraform Init
- Terraform Plan
- Evaluate Policy
- Terraform Apply
- Archive State for Account

### Provision Signals

- Human Approval
- Human Denial

### Provision Queries

- Get Progress

## TODO

- Clear TODOs, more comments all over, no prints, linting, final README
- Use custom search attributes to publish the status
- Failure conditions
- Test queries
- SDK metrics / Grafana integration
- UI
- Workflow diagram
- Ephemeral Infrastructure w/ keepalives on the TTL
- Codec Server (sharing a TCLD api key)

## Ideas

- Public Module Registry
- Get certs for the runs from a local Vault instance? Generate with TF?
- CDK TF Python?
- Use local activities for terraform stuff and normal activities for API checks?
- Compensations?
- Destroy workflow
- GH actions
- OPA

## Questions

- Do we want to block admins in namespaces as well? Any other valuable policy?
- Do we want to take arguments for each namespace in the .tf files or keep them declarative?
- Do we want to generate certs with Vault? Or generate here in the TF?
- Is this something we want to use for ephermeral scale testing environments?
- Do we want to make this save statefiles / planfiles across runs? Is this valuable enough?

## Notes

- Setting the insecure flag in the TF config led to an irrecoverable HTTP/2 error.
