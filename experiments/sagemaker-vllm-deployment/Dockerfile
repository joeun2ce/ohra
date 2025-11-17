FROM vllm/vllm-openai:latest AS vllm-base

# Create a new stage based on vllm-base
FROM vllm-base AS sagemaker-serving

# Copy the SageMaker serving script
COPY src/sagemaker_serving.py /app/sagemaker_serving.py

# Copy the serve entrypoint script
COPY scripts/serve /usr/bin/serve

# Set the working directory
WORKDIR /app

# Ensure the serve script has executable permissions
RUN chmod +x /usr/bin/serve

# Expose port 8080 (required by SageMaker)
EXPOSE 8080

# Set the serve script as the entrypoint
ENTRYPOINT ["/usr/bin/serve"]
