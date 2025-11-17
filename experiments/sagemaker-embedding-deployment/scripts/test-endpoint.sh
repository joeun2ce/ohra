#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
fi

ENDPOINT_NAME="${ENDPOINT_NAME:-your-endpoint-name}"
REGION="${AWS_REGION:-ap-northeast-2}"

SYSTEM="${SYSTEM:-You are a helpful assistant.}"
USER="${USER:-Say hello in Korean.}"

TMP_DIR="$(mktemp -d)"
REQ="${TMP_DIR}/request.json"
RES="${TMP_DIR}/response.json"

# reacte json
cat > "$REQ" << JSON
{
  "inputs": "<|im_start|>system\n${SYSTEM}<|im_end|>\n<|im_start|>user\n${USER}<|im_end|>\n<|im_start|>assistant\n",
  "parameters": {
    "max_new_tokens": 128,
    "temperature": 0.7,
    "top_p": 0.9,
    "stop": ["<|im_end|>", "<|endoftext|>"]
  },
  "stream": false
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
