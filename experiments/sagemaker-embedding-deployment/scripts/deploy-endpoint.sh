#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env
if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
else
  echo "Error: .env file not found. Copy .env.example to .env and configure."
  exit 1
fi

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
ECR_IMAGE_URI="${ECR_IMAGE_URI:-}"

MODEL_NAME="${MODEL_NAME:-your-model-name}"
ENDPOINT_CONFIG_NAME="${ENDPOINT_CONFIG_NAME:-your-endpoint-config-name}"
ENDPOINT_NAME="${ENDPOINT_NAME:-your-endpoint-name}"

SAGEMAKER_ROLE_ARN="${SAGEMAKER_ROLE_ARN:-}"
VPC_ID="${VPC_ID:-}"
SUBNET_IDS="${SUBNET_IDS:-}"
SG_IDS="${SG_IDS:-}"

INSTANCE_TYPE="${INSTANCE_TYPE:-ml.g5.xlarge}"
INITIAL_INSTANCE_COUNT="${INITIAL_INSTANCE_COUNT:-1}"
CONTAINER_STARTUP_TIMEOUT="${CONTAINER_STARTUP_TIMEOUT:-600}"

if [[ "${#}" -ge 1 && -n "${1:-}" ]]; then
  ECR_IMAGE_URI="$1"
fi

echo_info() { echo -e "\033[0;32m[INFO]\033[0m $*"; }
echo_err()  { echo -e "\033[0;31m[ERR]\033[0m  $*"; }

# Preflight
command -v aws >/dev/null || { echo_err "AWS CLI not found"; exit 1; }

if [[ -z "${ECR_IMAGE_URI}" ]]; then
  echo_err "ECR_IMAGE_URI is empty. Set it in .env file or pass as argument."
  echo "Example: ./scripts/deploy-endpoint.sh <ECR_IMAGE_URI>"
  exit 1
fi

echo_info "Region: ${AWS_REGION}"
echo_info "Image: ${ECR_IMAGE_URI}"
echo_info "Model: ${MODEL_NAME}"
echo_info "EndpointConfig: ${ENDPOINT_CONFIG_NAME}"
echo_info "Endpoint: ${ENDPOINT_NAME}"
if [[ -n "${SUBNET_IDS}" && -n "${SG_IDS}" ]]; then
  echo_info "VPC: ${VPC_ID} | Subnets: ${SUBNET_IDS} | SGs: ${SG_IDS}"
else
  echo_info "VPC: Not configured (using default VPC)"
fi
echo_info "Instance: ${INSTANCE_TYPE} x ${INITIAL_INSTANCE_COUNT}"
echo_info "Startup timeout: ${CONTAINER_STARTUP_TIMEOUT}s"

# Create Model
echo_info "Creating SageMaker model: ${MODEL_NAME}"
MODEL_ARGS=(
  --region "${AWS_REGION}"
  --model-name "${MODEL_NAME}"
  --primary-container Image="${ECR_IMAGE_URI}"
  --execution-role-arn "${SAGEMAKER_ROLE_ARN}"
)

# Only add VPC config if both SUBNET_IDS and SG_IDS are provided
if [[ -n "${SUBNET_IDS}" && -n "${SG_IDS}" ]]; then
  MODEL_ARGS+=(--vpc-config "Subnets=${SUBNET_IDS},SecurityGroupIds=${SG_IDS}")
fi

aws sagemaker create-model "${MODEL_ARGS[@]}" >/dev/null
echo_info "Model created."

# Create Endpoint Config
echo_info "Creating endpoint config: ${ENDPOINT_CONFIG_NAME}"
aws sagemaker create-endpoint-config \
  --region "${AWS_REGION}" \
  --endpoint-config-name "${ENDPOINT_CONFIG_NAME}" \
  --production-variants "[
    {
      \"VariantName\": \"AllTraffic\",
      \"ModelName\": \"${MODEL_NAME}\",
      \"InitialInstanceCount\": ${INITIAL_INSTANCE_COUNT},
      \"InstanceType\": \"${INSTANCE_TYPE}\",
      \"InitialVariantWeight\": 1.0,
      \"ContainerStartupHealthCheckTimeoutInSeconds\": ${CONTAINER_STARTUP_TIMEOUT}
    }
  ]" \
  >/dev/null
echo_info "Endpoint config created."

# Create Endpoint
echo_info "Creating endpoint: ${ENDPOINT_NAME}"
aws sagemaker create-endpoint \
  --region "${AWS_REGION}" \
  --endpoint-name "${ENDPOINT_NAME}" \
  --endpoint-config-name "${ENDPOINT_CONFIG_NAME}" \
  >/dev/null

echo_info "Waiting for endpoint InService (this can take several minutes)..."
aws sagemaker wait endpoint-in-service \
  --region "${AWS_REGION}" \
  --endpoint-name "${ENDPOINT_NAME}"
echo_info "Endpoint is InService."

# Test Inference
TMP_DIR="$(mktemp -d)"
REQ="${TMP_DIR}/payload.json"
OUT="${TMP_DIR}/out.json"

cat > "${REQ}" << 'JSON'
{
  "inputs": "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nSay hello in Korean.<|im_end|>\n<|im_start|>assistant\n",
  "parameters": {
    "max_new_tokens": 128,
    "temperature": 0.7,
    "top_p": 0.9,
    "stop": ["<|im_end|>", "<|endoftext|>"]
  },
  "stream": false
}
JSON

echo_info "Invoking endpoint (non-streaming)..."
aws sagemaker-runtime invoke-endpoint --region "${AWS_REGION}" --endpoint-name "${ENDPOINT_NAME}" --content-type "application/json" --body "fileb://${REQ}" "${OUT}" >/dev/null

echo_info "Raw response (JSON):"
cat "${OUT}"
echo
echo_info "Done. Temp files at: ${TMP_DIR}"