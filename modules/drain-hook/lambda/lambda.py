import functools
import json
import os

import boto3

CLUSTER = os.environ["CLUSTER"]
QUEUE_URL = os.environ["QUEUE_URL"]

autoscaling_client = boto3.client("autoscaling")
ecs_client = boto3.client("ecs")
sqs_client = boto3.client("sqs")


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


@functools.lru_cache(maxsize=1024)
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

    # The event will contain a list of SQS records/messages. The Lambda
    # event source mapping batch size is set to 1, so there will always
    # be 1 record. The record will contain a single CloudWatch event for
    # an instance which is being terminated.

    log = LambdaLogger(context)

    sqs_message = event["Records"][0]
    message_id = sqs_message["messageId"]
    message_body = sqs_message["body"]

    log["MessageId"] = message_id
    log.info("Processing message")

    cloudwatch_event = json.loads(message_body)
    asg_name = cloudwatch_event["detail"]["AutoScalingGroupName"]
    instance_id = cloudwatch_event["detail"]["EC2InstanceId"]
    lifecycle_hook_name = cloudwatch_event["detail"]["LifecycleHookName"]

    log["InstanceId"] = instance_id
    log.info("Processing instance termination event")

    # Get the container instance ARN for this EC2 instance.
    container_instance_arn = get_container_instance_arn(instance_id)
    if container_instance_arn:

        log["ContainerInstanceArn"] = container_instance_arn

        # Get the container instance details.
        instance = get_container_instance(container_instance_arn)
        if instance:

            tasks_count = instance["pendingTasksCount"] + instance["runningTasksCount"]

            log["TasksCount"] = tasks_count

            # Ensure the instance is "draining",
            # so ECS will move tasks off this instance.
            if instance["status"] not in ("DRAINING", "DEREGISTERING"):
                log.info("Setting status to DRAINING")
                ecs_client.update_container_instances_state(
                    cluster=CLUSTER,
                    containerInstances=[instance["containerInstanceArn"]],
                    status="DRAINING",
                )

        else:
            log.info("Lookup failed in get_container_instance")
            tasks_count = None

    else:
        log.info("Lookup failed in get_container_instance_arn")
        tasks_count = None

    if tasks_count:

        # There are tasks on this instance so don't terminate it yet.
        # Record a lifecycle action heartbeat to extend the timeout so
        # it doesn't perform the default action (which might be to abandon
        # the termination and keep running, or it might be to continue
        # terminating the instance). Put the message back on the queue,
        # with a delay, to check the instance again later.

        log.info("Recording lifecycle action heartbeat")
        autoscaling_client.record_lifecycle_action_heartbeat(
            AutoScalingGroupName=asg_name,
            InstanceId=instance_id,
            LifecycleHookName=lifecycle_hook_name,
        )

        log.info("Sending message to check again later")
        sqs_client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=message_body,
            DelaySeconds=30,
        )

    else:

        # There are no tasks on this instance (the lookups returned zero
        # tasks or they failed) so let the autoscaling group terminate
        # the instance.

        log.info("Completing lifecycle action")
        autoscaling_client.complete_lifecycle_action(
            AutoScalingGroupName=asg_name,
            InstanceId=instance_id,
            LifecycleHookName=lifecycle_hook_name,
            LifecycleActionResult="CONTINUE",
        )
