# Temporal Cloud Onboarding Module

```bash
# authenticate your session
tcld login
# generate an API Key
tcld apikey create -n "terraform-test" --desc "Testing the API Key for the TF Provider" -d 90d
```

```bash
# replace <yoursecretkey> with the "secretKey": output from tcld apikey create command
export TEMPORAL_CLOUD_API_KEY="tmprl_EuInTzfBKYGI6xZQ9DHY2B9aVENaeOa7_R7uVJf0mQE7yfvLoYwQsx0TXiD4b9DnscOlewoS6BSIB0yS4OhZdXxf6vLJuuyfX"
```

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

