variable "asg_name" {
  type = string
}

variable "boot_timeout_seconds" {
  description = "The time allowed for instances to be drained before giving up."
  type        = number
  default     = 60 * 15
}

variable "ecs_cluster_name" {
  type = string
}

locals {
  name = "${var.asg_name}-boot"
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
}
