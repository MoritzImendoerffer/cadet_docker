#!/usr/bin/env python3
"""
deploy.py – Build, push, and roll out a new Cadet-API image using boto3.

Usage:
    python deploy.py \
        --region eu-central-1 \
        --ecr-repo cadet-api-prod \
        --cluster cadetCluster \
        --service cadetService \
        --tag prod
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def run(cmd: str) -> None:
    """Run a shell command, streaming stdout/stderr, abort on error."""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build_and_push_image(ecr_uri: str, tag: str, region: str) -> None:
    full_uri = f"{ecr_uri}:{tag}"
    print(f"Building image {full_uri}")
    run(f"DOCKER_BUILDKIT=1 docker build -f Dockerfile_ubuntu -t {full_uri} .")

    print("Logging into ECR")
    login_pw = (
        boto3.client("ecr", region_name=region)
        .get_authorization_token()["authorizationData"][0]["authorizationToken"]
    )
    run(
        f"echo {login_pw} | base64 -d | "
        f"cut -d: -f2 | docker login -u AWS --password-stdin {ecr_uri}"
    )

    print("Pushing image")
    run(f"docker push {full_uri}")


def update_ecs_service(region: str, cluster: str, service: str, image_uri: str) -> None:
    ecs = boto3.client("ecs", region_name=region)

    # fetch current task-definition
    svc = ecs.describe_services(cluster=cluster, services=[service])["services"][0]
    task_arn = svc["taskDefinition"]
    family = task_arn.split("/")[-1].split(":")[0]

    td = ecs.describe_task_definition(taskDefinition=task_arn)["taskDefinition"]

    # mutate container image
    td["containerDefinitions"][0]["image"] = image_uri

    # strip read-only keys per ECS API
    for key in (
        "taskDefinitionArn",
        "revision",
        "status",
        "requiresAttributes",
        "compatibilities",
        "registeredAt",
        "registeredBy",
    ):
        td.pop(key, None)

    print("Registering new task-definition revision")
    new_td = ecs.register_task_definition(**td)["taskDefinition"]["taskDefinitionArn"]
    print(f"   → {new_td}")

    print("Forcing new deployment")
    ecs.update_service(
        cluster=cluster, service=service, taskDefinition=new_td, forceNewDeployment=True
    )
    print("Deployment triggered")


# --------------------------------------------------------------------------- #
# Entry-point                                                                 #
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--ecr-repo", required=True)
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--tag", default="prod")
    args = parser.parse_args()

    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    ecr_uri = f"{account_id}.dkr.ecr.{args.region}.amazonaws.com/{args.ecr_repo}"
    image_uri = f"{ecr_uri}:{args.tag}"

    # ensure repository exists
    ecr = boto3.client("ecr", region_name=args.region)
    try:
        ecr.describe_repositories(repositoryNames=[args.ecr_repo])
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "RepositoryNotFoundException":
            print("Creating ECR repository")
            ecr.create_repository(repositoryName=args.ecr_repo)
        else:
            raise

    build_and_push_image(ecr_uri, args.tag, args.region)
    update_ecs_service(args.region, args.cluster, args.service, image_uri)


if __name__ == "__main__":
    main()
