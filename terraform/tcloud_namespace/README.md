# Temporal Cloud Onboarding Module

For the Terraform to successfully authenticate against Temporal Cloud, you will need an API key. Use the below commands to generate one.

```bash
# authenticate your session
tcld login
# generate an API Key
tcld apikey create -n "terraform-test" --desc "Testing the API Key for the TF Provider" -d 90d
```

Then set your `TEMPORAL_API_KEY` environment variable.

```bash
# replace <yoursecretkey> with the "secretKey": output from tcld apikey create command
export TEMPORAL_API_KEY=""
```

Once you have set your `TEMPORAL_API_KEY` environment variable, initialize the Terraform configuration.

```bash
terraform init
```

To see a dry run of what changes this Terraform run will make, use `plan`.

```bash
terraform plan
```

Then apply the changes with `apply`.

```bash
terraform apply
```

When you ready to clean up everything you have provisioned, you can `destroy`. Be careful, this is a destructive action.

```bash
terraform destroy
```
