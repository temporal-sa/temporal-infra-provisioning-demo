#!/bin/sh

TEMPORAL_ENV="<cli_env_name>"

export TEMPORAL_ADDRESS=$(temporal env get --env ${TEMPORAL_ENV} --key address -o json | jq -r '.[].value')
export TEMPORAL_NAMESPACE=$(temporal env get --env ${TEMPORAL_ENV} --key namespace -o json | jq -r '.[].value')
export TEMPORAL_CERT_PATH=$(temporal env get --env ${TEMPORAL_ENV} --key tls-cert-path -o json | jq -r '.[].value')
export TEMPORAL_KEY_PATH=$(temporal env get --env ${TEMPORAL_ENV} --key tls-key-path -o json | jq -r '.[].value')

# Required
export TEMPORAL_CLOUD_API_KEY="<temporal_cloud_api_key>"
export TF_VAR_prefix="<your_name>"

# Optional
export TEMPORAL_ADDRESS="host.docker.internal:7233" # For Docker workers
export TEMPORAL_TASK_QUEUE="<task_queue_name>"
export TEMPORAL_MTLS_DIR="<path_to_mtls_certs>"
export ENCRYPT_PAYLOADS=true
