variable "asg_name" {
  type = string
}

variable "drain_timeout_seconds" {
  description = "The time allowed for instances to be drained before giving up."
  type        = number
  default     = 60 * 60
}

variable "ecs_cluster_name" {
  type = string
}

variable "lambda_timeout_seconds" {
  description = "The time allowed for the Lambda function to run."
  type        = number
  default     = 10
}

locals {
  name = "${var.asg_name}-drain"
  asg_arn = format(
    "arn:%s:autoscaling:%s:%s:autoScalingGroup:%s:autoScalingGroupName/%s",
    data.aws_partition.current.partition,
    data.aws_region.current.name,
    data.aws_caller_identity.current.account_id,
    "*",
    var.asg_name,
  )
  ecs_cluster_arn = format(
    "arn:%s:ecs:%s:%s:cluster/%s",
    data.aws_partition.current.partition,
    data.aws_region.current.name,
    data.aws_caller_identity.current.account_id,
    var.ecs_cluster_name,
  )
  event_rule_arn = format(
    "arn:%s:events:%s:%s:rule/%s",
    data.aws_partition.current.partition,
    data.aws_region.current.name,
    data.aws_caller_identity.current.account_id,
    local.name,
  )
  sqs_queue_arn = format(
    "arn:%s:sqs:%s:%s:%s",
    data.aws_partition.current.partition,
    data.aws_region.current.name,
    data.aws_caller_identity.current.account_id,
    local.name,
  )
}
