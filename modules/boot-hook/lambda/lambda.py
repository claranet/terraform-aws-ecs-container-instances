import json
import os
import time

import boto3

CLUSTER = os.environ["CLUSTER"]


autoscaling_client = boto3.client("autoscaling")
ecs_client = boto3.client("ecs")


class LambdaLogger:
    def __init__(self, context):
        self.context = context
        self.extra = {}

    def __setitem__(self, key, value):
        self.extra[key] = value

    def info(self, message):
        parts = ["INFO", "RequestId:", self.context.aws_request_id, message]
        if self.extra:
            parts.append(json.dumps(self.extra))
        print(" ".join(parts))


def get_container_instance(container_instance_arn):
    response = ecs_client.describe_container_instances(
        cluster=CLUSTER,
        containerInstances=[container_instance_arn],
    )
    for instance in response["containerInstances"]:
        return instance
    else:
        return None


def get_container_instance_arn(instance_id):
    response = ecs_client.list_container_instances(
        cluster=CLUSTER,
        filter=f"ec2InstanceId == {instance_id}",
    )
    for arn in response["containerInstanceArns"]:
        return arn
    else:
        return None


def lambda_handler(event, context):

    log = LambdaLogger(context)

    asg_name = event["detail"]["AutoScalingGroupName"]
    instance_id = event["detail"]["EC2InstanceId"]
    lifecycle_hook_name = event["detail"]["LifecycleHookName"]

    log["InstanceId"] = instance_id
    log.info("Processing instance launch event")

    # Get the ECS container instance ARN from the EC2 instance ID.
    # This will only work if/once the ECS agent on the instance has
    # started and successfully joined the ECS cluster, so keep checking.
    while True:
        container_instance_arn = get_container_instance_arn(instance_id)
        if container_instance_arn:
            log["ContainerInstanceArn"] = container_instance_arn
            break
        else:
            log.info("Waiting for container instance ARN")
            time.sleep(15)

    # Keep checking the ECS container instance status until it is ACTIVE.
    # This Lambda function will time out if it never becomes ACTIVE.
    # In that case, the ASG lifecycle hook will time out and abandon
    # the instance, causing it to be terminated.
    while True:
        instance = get_container_instance(container_instance_arn)
        status = instance["status"]
        log["Status"] = status
        status_reason = instance.get("statusReason")
        if status_reason:
            log["StatusReason"] = status_reason
        if status == "ACTIVE":
            break
        else:
            log["StatusReason"] = instance.get("statusReason")
            log.info("Waiting for status to become ACTIVE")
            time.sleep(15)

    # The container instance is active and accepting tasks,
    # so complete the lifecycle action.
    log.info("Completing lifecycle action")
    autoscaling_client.complete_lifecycle_action(
        AutoScalingGroupName=asg_name,
        InstanceId=instance_id,
        LifecycleHookName=lifecycle_hook_name,
        LifecycleActionResult="CONTINUE",
    )
