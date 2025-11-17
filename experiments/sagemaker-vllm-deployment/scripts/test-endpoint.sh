#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
fi

ENDPOINT_NAME="${ENDPOINT_NAME:-vllm-endpoint}"
REGION="${AWS_REGION:-ap-northeast-2}"

SYSTEM="${SYSTEM:-You are a helpful assistant.}"
USER="${USER:-Say hello in Korean.}"

TMP_DIR="$(mktemp -d)"
REQ="${TMP_DIR}/request.json"
RES="${TMP_DIR}/response.json"

# Create request JSON (OpenAI 호환 형식)
cat > "$REQ" << JSON
{
  "model": "${MODEL_ID:-Qwen/Qwen3-4B-Instruct-2507}",
  "messages": [
    {"role": "system", "content": "${SYSTEM}"},
    {"role": "user", "content": "${USER}"}
  ],
  "max_tokens": 128,
  "temperature": 0.7,
  "top_p": 0.9
}
JSON

echo "Invoking endpoint: $ENDPOINT_NAME"
echo "Request:"
cat "$REQ" | jq .
echo ""

aws sagemaker-runtime invoke-endpoint \
  --region "$REGION" \
  --endpoint-name "$ENDPOINT_NAME" \
  --content-type "application/json" \
  --body "fileb://$REQ" \
  "$RES" >/dev/null

echo "Response:"
cat "$RES" | jq .

echo ""
echo "Cleanup: rm -rf $TMP_DIR"

