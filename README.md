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
- If admin is being generated, then require approval from a human
- Create failure conditios
- Add a step to archive state
- Use local activities for terraform stuff and normal activities for API checks?
- Add venv instructions or use poetry
- remove all TODOs
- Have a separate workflow for destroy, do a signal check or multiple when destroying
- Put a module on the Public Module Registry?
- Terraform destroy on failure
- Review all the types that I'm using
- Terraform apply is synchronous for the most part?

## Notes

- Setting the insecure flag in the TF config led to an irrecoverable HTTP/2 error.
