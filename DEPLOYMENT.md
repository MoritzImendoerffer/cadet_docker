# Deployment Guide – FastAPI + CADET on AWS Fargate

This guide describes how to deploy the FastAPI-based CADET simulation microservice to **AWS Fargate**, using **AWS Secrets Manager** to securely manage cryptographic keys.

---

## Prerequisites

* AWS CLI installed and configured (`aws configure`)
* Docker installed
* A VPC with public subnets and security groups
* An IAM role (`ecsTaskExecutionRole`) with `secretsmanager:GetSecretValue` permissions

---

## Contents

* [1. Build and Push Docker Image](#1-build-and-push-docker-image)
* [2. Upload Server Keys to AWS Secrets Manager](#2-upload-server-keys-to-aws-secrets-manager)
* [3. Create ECS Task Definition](#3-create-ecs-task-definition)
* [4. Run the ECS Service on Fargate](#4-run-the-ecs-service-on-fargate)
* [5. Access the API](#5-access-the-api)
* [6. Optional: Managing Client Keys in AWS](#6-optional-managing-client-keys-in-aws)

---

## 1. Build and Push Docker Image

### Authenticate Docker with ECR

```bash
aws ecr get-login-password \
  | docker login --username AWS \
    --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
```

### Build the image

```bash
docker build -t cadet-api .
```

### Create ECR repository

```bash
aws ecr create-repository --repository-name cadet-api
```

### Tag and push the image

```bash
docker tag cadet-api:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/cadet-api:latest

docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/cadet-api:latest
```

---

## 2. Upload Server Keys to AWS Secrets Manager

Assumes your keys are located in `~/.cadet_api/`:

```bash
aws secretsmanager create-secret \
  --name cadet-api-private-key \
  --secret-string file://~/.cadet_api/private_key.pem

aws secretsmanager create-secret \
  --name cadet-api-public-key \
  --secret-string file://~/.cadet_api/public_key.pem
```

---

## 3. Create ECS Task Definition

### ✅ Create `task-def.json`

```json
{
  "family": "cadet-api-task",
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "<ecsTaskExecutionRole ARN>",
  "containerDefinitions": [
    {
      "name": "cadet-api",
      "image": "<aws_account_id>.dkr.ecr.<region>.amazonaws.com/cadet-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "secrets": [
        {
          "name": "PRIVATE_KEY_PEM",
          "valueFrom": "arn:aws:secretsmanager:<region>:<account_id>:secret:cadet-api-private-key"
        },
        {
          "name": "PUBLIC_KEY_PEM",
          "valueFrom": "arn:aws:secretsmanager:<region>:<account_id>:secret:cadet-api-public-key"
        }
      ],
      "environment": [
        {
          "name": "CLIENT_KEYS_DIR",
          "value": "/app/client_keys"
        }
      ]
    }
  ]
}
```

### Register the task

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-def.json
```

---

## 4. Run the ECS Service on Fargate

### Create the cluster

```bash
aws ecs create-cluster --cluster-name cadet-cluster
```

### Deploy the service

```bash
aws ecs create-service \
  --cluster cadet-cluster \
  --service-name cadet-api-service \
  --task-definition cadet-api-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=ENABLED}"
```

---

## 5. Access the API

Once the task is running, you can:

* Locate the **public IP address** of the task via the ECS Console (Networking tab)
* Then test it:

```bash
curl http://<public-ip>:8000/public_key
```

---

## 6. Optional: Managing Client Keys in AWS

To store client keys in AWS Secrets Manager:

1. Upload a client public key:

```bash
aws secretsmanager create-secret \
  --name client-acme-pub \
  --secret-string file://acme.pem
```

2. Modify your app to load from Secrets:

```python
boto3.client("secretsmanager").get_secret_value(
    SecretId=f"client-{client_id}-pub"
)["SecretString"]
```

Alternatively, bundle all client keys in your Docker image under `/app/client_keys`.

---

## Summary

| Task                                          | Status |
| --------------------------------------------- | ------ |
| Docker image built & pushed                   | [x]      |
| Secrets uploaded to AWS                       | [x]      |
| Task definition created with secret injection | [x]      |
| Service deployed to Fargate                   | [x]      |
| App accessed via public IP                    | [x]      |

---
