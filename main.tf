module "instance_profile" {
  source = "git::https://gitlab.com/claranet-pcp/terraform/aws/tf-aws-iam-instance-profile.git?ref=v6.0.0"

  name = "${var.cluster_name}-ec2"

  aws_policies        = ["service-role/AmazonEC2ContainerServiceforEC2Role"]
  ssm_managed         = true
  ssm_session_manager = true
}

resource "aws_security_group" "this" {
  name   = "${var.cluster_name}-ec2"
  vpc_id = var.vpc_id
}

resource "aws_security_group_rule" "egress" {
  security_group_id = aws_security_group.this.id
  type              = "egress"
  protocol          = -1
  from_port         = 0
  to_port           = 0
  cidr_blocks       = ["0.0.0.0/0"]
}

module "asg" {
  source = "github.com/claranet/terraform-aws-asg-pipeline//modules/asg?ref=v2.0.0"

  depends_on = [module.boot_instances, module.drain_instances]

  ami_pipeline            = true
  instance_profile_arn    = module.instance_profile.profile_arn
  instance_type           = var.instance_type
  max_size                = var.max_size
  min_size                = 0 # ECS capacity provider auto scaling will scale up from zero
  name                    = local.asg_name
  pipeline_target_name    = var.pipeline_target_name
  pipeline_auto_deploy    = var.pipeline_auto_deploy
  pipeline_aws_account_id = var.pipeline_aws_account_id
  security_group_ids      = [aws_security_group.this.id]
  subnet_ids              = var.subnet_ids
  user_data               = var.user_data

  lifecycle_hooks = [
    {
      LifecycleHookName   = local.asg_hook_boot
      LifecycleTransition = "autoscaling:EC2_INSTANCE_LAUNCHING"
      HeartbeatTimeout    = var.boot_timeout_seconds
      DefaultResult       = "ABANDON"
    },
    {
      LifecycleHookName   = local.asg_hook_drain
      LifecycleTransition = "autoscaling:EC2_INSTANCE_TERMINATING"
      HeartbeatTimeout    = var.drain_timeout_seconds
      DefaultResult       = "ABANDON"
    },
  ]

  tags = merge(var.tags, {
    AmazonECSManaged = "" # required by ECS capacity provider
  })
}

resource "aws_ecs_capacity_provider" "asg" {
  name = module.asg.asg_name

  auto_scaling_group_provider {
    auto_scaling_group_arn         = module.asg.asg_arn
    managed_termination_protection = "DISABLED"

    managed_scaling {
      maximum_scaling_step_size = 10000 # scaling is still limited by ASG max size
      minimum_scaling_step_size = 1
      status                    = "ENABLED"
      target_capacity           = 100
    }
  }
}

module "boot_instances" {
  source = "./modules/boot-hook"

  asg_name             = local.asg_name
  boot_timeout_seconds = var.boot_timeout_seconds
  ecs_cluster_name     = var.cluster_name
}

module "drain_instances" {
  source = "./modules/drain-hook"

  asg_name              = local.asg_name
  drain_timeout_seconds = var.drain_timeout_seconds
  ecs_cluster_name      = var.cluster_name
}

module "cloudwatch_agent" {
  source = "./modules/cloudwatch-agent-daemon-service"

  cluster_name = var.cluster_name
}
