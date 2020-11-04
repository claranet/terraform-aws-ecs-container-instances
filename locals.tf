locals {
  asg_name = var.cluster_name

  asg_hook_boot  = "boot"
  asg_hook_drain = "drain"

  cluster_arn = format(
    "arn:%s:ecs:%s:%s:cluster/%s",
    data.aws_partition.current.partition,
    data.aws_region.current.name,
    data.aws_caller_identity.current.account_id,
    var.cluster_name,
  )
}
