resource "aws_cloudwatch_event_rule" "this" {
  name = local.name
  event_pattern = jsonencode({
    source      = ["aws.autoscaling"]
    detail-type = ["EC2 Instance-terminate Lifecycle Action"]
    detail = {
      AutoScalingGroupName = [var.asg_name]
    }
  })
}

resource "aws_cloudwatch_event_target" "this" {
  target_id = "lambda"
  rule      = aws_cloudwatch_event_rule.this.name
  arn       = aws_sqs_queue.this.arn
}

# Some SQS queue settings are recommended here:
# https://docs.aws.amazon.com/en_gb/lambda/latest/dg/with-sqs.html

resource "aws_sqs_queue" "this" {
  name                      = local.name
  message_retention_seconds = var.drain_timeout_seconds
  policy                    = data.aws_iam_policy_document.sqs.json
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5 # as recommended
  })
  visibility_timeout_seconds = var.lambda_timeout_seconds * 6 # as recommended
}

data "aws_iam_policy_document" "sqs" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions   = ["sqs:SendMessage"]
    resources = [local.sqs_queue_arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [local.event_rule_arn]
    }
  }
}

# The dead letter queue only exists in case messages repeatedly fail
# to be processed and need to be removed from the main processing queue.
# Messages in this queue will be automatically deleted after a few days.

resource "aws_sqs_queue" "dlq" {
  name = "${local.name}-dlq"
}

resource "aws_lambda_event_source_mapping" "this" {
  batch_size       = 1
  event_source_arn = aws_sqs_queue.this.arn
  enabled          = true
  function_name    = module.lambda.function_name
}

module "lambda" {
  source  = "raymondbutcher/lambda-builder/aws"
  version = "1.1.0"

  function_name = local.name
  handler       = "lambda.lambda_handler"
  runtime       = "python3.7"
  memory_size   = 128
  timeout       = var.lambda_timeout_seconds

  build_mode = "FILENAME"
  source_dir = "${path.module}/lambda"
  filename   = "${path.module}/lambda.zip"

  role_cloudwatch_logs       = true
  role_custom_policies       = [data.aws_iam_policy_document.lambda.json]
  role_custom_policies_count = 1

  environment = {
    variables = {
      CLUSTER   = var.ecs_cluster_name
      QUEUE_URL = aws_sqs_queue.this.id
    }
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    effect = "Allow"
    actions = [
      "autoscaling:CompleteLifecycleAction",
      "autoscaling:RecordLifecycleActionHeartbeat",
    ]
    resources = [local.asg_arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["ecs:ListContainerInstances"]
    resources = [local.ecs_cluster_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecs:DescribeContainerInstances",
      "ecs:UpdateContainerInstancesState",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "ecs:cluster"
      values   = [local.ecs_cluster_arn]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ReceiveMessage",
      "sqs:SendMessage",
    ]
    resources = [local.sqs_queue_arn]
  }
}
