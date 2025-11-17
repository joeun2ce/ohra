#!/bin/bash

# Color definitions for beautiful logging
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m' # No Color

# ──────────────────────────────────────────────
# Configuration
REPOSITORY="ohra/worker-sync"
TIMESTAMP=$(date '+%Y-%m-%d-%H-%M-%S')
RUNTIME_VERSION="python3.12"
TAG="${RUNTIME_VERSION}-${TIMESTAMP}"
FULL_IMAGE_NAME="${REPOSITORY}:${TAG}"

echo -e "${CYAN}${BOLD}───────────────────────────────────────────────${NC}"
echo -e "${GREEN}${BOLD} OHRA Worker Sync Docker Build${NC}"
echo -e "${CYAN}${BOLD}───────────────────────────────────────────────${NC}"
echo -e "${YELLOW}Repository: ${WHITE}${REPOSITORY}${NC}"
echo -e "${YELLOW}Image Tag:  ${WHITE}${TAG}${NC}"
echo -e "${CYAN}${BOLD}───────────────────────────────────────────────${NC}"
echo -e "${BLUE}▶️  Docker build 시작...${NC}"

DOCKER_BUILDKIT=1 docker build \
    -f ./docker/Dockerfile \
    -t ${FULL_IMAGE_NAME} \
    ../../

BUILD_RESULT=$?

if [ $BUILD_RESULT -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ Build Success!${NC}"
    echo -e "${PURPLE}Image: ${WHITE}${FULL_IMAGE_NAME}${NC}"
else
    echo -e "${RED}${BOLD}❌ Build Failed!${NC}"
    exit 1
fi

echo -e "${CYAN}${BOLD}───────────────────────────────────────────────${NC}"

