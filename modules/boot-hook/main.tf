resource "aws_cloudwatch_event_rule" "this" {
  name = local.name
  event_pattern = jsonencode({
    source      = ["aws.autoscaling"]
    detail-type = ["EC2 Instance-launch Lifecycle Action"]
    detail = {
      AutoScalingGroupName = [var.asg_name]
    }
  })
}

resource "aws_cloudwatch_event_target" "this" {
  target_id = "lambda"
  rule      = aws_cloudwatch_event_rule.this.name
  arn       = module.lambda.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "cloudwatch-event-rule"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}

module "lambda" {
  source  = "raymondbutcher/lambda-builder/aws"
  version = "1.1.0"

  function_name = local.name
  handler       = "lambda.lambda_handler"
  runtime       = "python3.7"
  memory_size   = 128
  timeout       = 60 * 15

  build_mode = "FILENAME"
  source_dir = "${path.module}/lambda"
  filename   = "${path.module}/lambda.zip"

  role_cloudwatch_logs       = true
  role_custom_policies       = [data.aws_iam_policy_document.lambda.json]
  role_custom_policies_count = 1

  environment = {
    variables = {
      CLUSTER = var.ecs_cluster_name
    }
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    effect = "Allow"
    actions = [
      "autoscaling:CompleteLifecycleAction",
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
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "ecs:cluster"
      values   = [local.ecs_cluster_arn]
    }
  }
}
