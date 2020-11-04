output "asg_name" {
  value = module.asg.asg_name
}

output "capacity_provider" {
  value = aws_ecs_capacity_provider.asg.name
}

output "pipeline_target" {
  value = module.asg.pipeline_target
}
