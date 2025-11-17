#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env
if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
else
  echo "Error: .env file not found. Copy .env.example to .env and configure."
  exit 1
fi

# Configuration
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
ECR_REPOSITORY="${ECR_REPOSITORY:-vllm-sagemaker-inference}"
IMAGE_TAG="${IMAGE_TAG:-v0.1.0}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-.}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error(){ echo -e "${RED}[ERROR]${NC} $1"; }

LOCAL_TAG="$ECR_REPOSITORY:$IMAGE_TAG"
ECR_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"

# Prereq
echo_info "Checking AWS CLI..."
command -v aws >/dev/null || { echo_error "AWS CLI not found."; exit 1; }
echo_info "Checking Docker..."
command -v docker >/dev/null || { echo_error "Docker not found."; exit 1; }

# Info
echo_info "AWS Account ID: $AWS_ACCOUNT_ID"
echo_info "AWS Region: $AWS_REGION"
echo_info "ECR Repository: $ECR_REPOSITORY"
echo_info "Dockerfile: $DOCKERFILE"
echo_info "Context: $BUILD_CONTEXT"
echo_info "Target image: $ECR_IMAGE"

# Ensure repo exists
echo_info "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null 2>&1 || \
aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" --image-scanning-configuration scanOnPush=true >/dev/null

# Login to ECR
echo_info "Logging in to your ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com" >/dev/null

# Build
if docker buildx version >/dev/null 2>&1; then
  echo_info "Building (buildx) linux/amd64 with schema2 (type=docker): $LOCAL_TAG"
  docker buildx build \
    --platform linux/amd64 \
    --output=type=docker \
    -t "$LOCAL_TAG" \
    -f "$PROJECT_ROOT/$DOCKERFILE" "$PROJECT_ROOT/$BUILD_CONTEXT"
else
  echo_warn "docker buildx not found. Falling back to classic build."
  DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t "$LOCAL_TAG" -f "$PROJECT_ROOT/$DOCKERFILE" "$PROJECT_ROOT/$BUILD_CONTEXT"
fi

# Tag & Push
echo_info "Tag & push to ECR..."
docker tag "$LOCAL_TAG" "$ECR_IMAGE"
docker push "$ECR_IMAGE" >/dev/null

# Verify manifest media type
check_media_type() {
  aws ecr batch-get-image \
    --region "$AWS_REGION" \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids imageTag="$IMAGE_TAG" \
    --query 'images[0].imageManifestMediaType' --output text 2>/dev/null
}

MEDIA_TYPE="$(check_media_type)"
echo_info "Image manifest media type: ${MEDIA_TYPE:-<empty>}"

# If not schema2, try skopeo convert to v2s2
if [[ "$MEDIA_TYPE" != "application/vnd.docker.distribution.manifest.v2+json" ]]; then
  echo_warn "Not docker schema2. Trying skopeo to convert to v2s2..."

  if ! command -v skopeo >/dev/null 2>&1; then
    echo_error "skopeo not installed. Install and re-run (macOS: brew install skopeo)."
    exit 1
  fi

  echo_info "Converting via skopeo (v2s2) and pushing..."
  skopeo copy --format v2s2 \
    --dest-creds "AWS:$(aws ecr get-login-password --region "$AWS_REGION")" \
    "docker-daemon:$LOCAL_TAG" \
    "docker://$ECR_IMAGE" >/dev/null

  MEDIA_TYPE="$(check_media_type)"
  echo_info "Image manifest media type after skopeo: ${MEDIA_TYPE:-<empty>}"
fi

if [[ "$MEDIA_TYPE" != "application/vnd.docker.distribution.manifest.v2+json" ]]; then
  echo_error "Still not docker schema2. Current: ${MEDIA_TYPE:-<empty>}. Aborting."
  exit 1
fi

# Done
echo_info "======================================"
echo_info "Deployment successful!"
echo_info "Image URI: $ECR_IMAGE"
echo_info "Use this in SageMaker model creation."
echo_info "======================================"
aws ecr describe-images --repository-name "$ECR_REPOSITORY" --image-ids imageTag="$IMAGE_TAG" --region "$AWS_REGION" --output table

