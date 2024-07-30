# temporal-infra-provisioning-demo

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

## Provision Workflow

### Provision Activities

- Load State for Account
- Terraform Init
- Terraform Plan (tail logs)
- Evaluate Policy
- Terraform Apply (only after approval, tail logs)
- Archive State for Account

### Provision Signals

- Human Approval

### Provision Queries

- Get Progress

## Destroy Workflow

### Destroy Activities

- Load State for Account
- Terraform Init
- Terraform Destroy (only after approval, tail logs)
- Archive State for Account

### Destroy Signals

- Human Approval

### Destroy Queries

- Get Progress

## TODO

- Default arguments / config
- Switch to Temporal logging, use more useful messages
- Implement in GH actions, use persistence across runs (are there versions of state?)
- Ensure I use all of the different primitives like the money transfer demo
- Create failure conditions
- Use local activities for terraform stuff and normal activities for API checks?
- Add venv instructions or use poetry
- Have a separate workflow for destroy, do a signal check or multiple when destroying
- Compensations?
- Review all the types that I'm using w/ modern Python
- Terraform apply is synchronous for the most part?
- Get certs for the runs from a local Vault instance? Generate with TF?

## Ideas

- Public Module Registry
- Ephemeral Infrastructure (teardown after set period of time unless signaled to keep alive from)

## Notes

- Setting the insecure flag in the TF config led to an irrecoverable HTTP/2 error.
