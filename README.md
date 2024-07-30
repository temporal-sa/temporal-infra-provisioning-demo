# temporal-infra-provisioning-demo

## Activities

- Select Terraform code to execute
- Check out code
- Terraform Plan
- Policy evaluation
- Cost estimation
- Human approval
- Terraform Apply
- Update progress bar

Terraform destroy on failure

## TODO

- Instructions for generating a token
- Switch to Temporal logging
- Implement in GH actions
- Ensure I use all of the different primitives like the money transfer demo
- Rename the module
- If admin is being generated, then require approval from a human
- Add a step to archive state
- Use local activities for terraform stuff and normal activities for API checks?
- Add venv instructions or use poetry
- Change from Provisioning to Terraform or vice a versa

## Notes

- Setting the insecure flag in the TF config led to an irrecoverable HTTP/2 error.

