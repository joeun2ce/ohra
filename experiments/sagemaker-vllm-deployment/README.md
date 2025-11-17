# SageMaker vLLM Deployment

vLLM을 직접 사용하여 SageMaker 엔드포인트에 배포하는 프로젝트입니다.

이 프로젝트는 [vllm-on-sagemaker](https://github.com/JianyuZhan/vllm-on-sagemaker) 리포지토리를 참고하여 구현되었습니다.

## 특징

- vLLM 공식 이미지 (`vllm/vllm-openai:latest`) 사용
- SageMaker 요구사항에 맞는 `/ping`과 `/invocations` 엔드포인트 구현
- OpenAI 호환 API 형식 요청 지원
- 인스턴스 타입에 따른 자동 GPU 수 감지 및 Tensor Parallelism 설정

## 구조

```
sagemaker-vllm-deployment/
├── src/
│   ├── sagemaker_serving.py  # FastAPI 서버 (SageMaker 엔드포인트 구현)
│   └── requirements.txt      # Python 의존성 (vLLM 이미지에 포함됨)
├── scripts/
│   ├── serve                 # SageMaker 엔트리포인트 스크립트
│   ├── build-and-push-image.sh  # Docker 이미지 빌드 및 ECR 푸시
│   ├── deploy-endpoint.sh       # SageMaker 엔드포인트 배포
│   └── test-endpoint.sh         # 엔드포인트 테스트
├── Dockerfile            # Docker 이미지 정의
└── README.md
```

## 사용 방법

### 1. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요:

```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 변경
```

```bash
AWS_REGION=ap-northeast-2
AWS_ACCOUNT_ID=your-account-id
ECR_REPOSITORY=vllm-sagemaker-inference
IMAGE_TAG=v0.1.0

SAGEMAKER_ROLE_ARN=arn:aws:iam::your-account-id:role/your-role
MODEL_NAME=vllm-model
ENDPOINT_CONFIG_NAME=vllm-endpoint-config
ENDPOINT_NAME=vllm-endpoint

INSTANCE_TYPE=ml.g5.12xlarge  # GPU 수는 자동 감지됨 (ml.g5.12xlarge = 4 GPUs)
INITIAL_INSTANCE_COUNT=1

# vLLM 설정
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507
# Tensor Parallelism은 INSTANCE_TYPE에 따라 자동 설정됨
```

### 2. Docker 이미지 빌드 및 푸시

```bash
./scripts/build-and-push-image.sh
```

### 3. 엔드포인트 배포

```bash
# 빌드 스크립트에서 출력된 이미지 URI를 사용
./scripts/deploy-endpoint.sh <ECR_IMAGE_URI>
```

### 4. 엔드포인트 테스트

```bash
./scripts/test-endpoint.sh
```

## 요청 형식

### OpenAI 호환 형식 (Chat Completion)

```json
{
  "model": "Qwen/Qwen3-4B-Instruct-2507",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Say hello in Korean."}
  ],
  "max_tokens": 128,
  "temperature": 0.7
}
```

## 환경 변수

서버는 다음 환경 변수를 통해 vLLM 설정을 받습니다:

- `MODEL_ID`: 모델 ID (필수)
- `INSTANCE_TYPE`: SageMaker 인스턴스 타입 (필수, GPU 수 자동 감지)
  - `ml.g5.4xlarge`: 1 GPU
  - `ml.g5.12xlarge`: 4 GPUs
  - `ml.g5.48xlarge`: 8 GPUs
  - `ml.p4d.24xlarge`: 8 GPUs (A100)
  - 기타 지원되는 인스턴스 타입
- `API_HOST`: API 호스트 (기본값: `0.0.0.0`)
- `API_PORT`: API 포트 (기본값: `8080`, SageMaker 요구사항)
- `PYTORCH_CUDA_ALLOC_CONF`: PyTorch CUDA 메모리 할당 설정 (기본값: `expandable_segments:True`)

Tensor Parallelism은 `INSTANCE_TYPE`에 따라 자동으로 설정됩니다.

