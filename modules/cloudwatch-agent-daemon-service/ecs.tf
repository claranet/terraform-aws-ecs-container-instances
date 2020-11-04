resource "aws_ecs_task_definition" "this" {
  family                   = "cwagent"
  cpu                      = 128
  memory                   = 64
  network_mode             = "bridge"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  volume {
    name      = "al1_cgroup"
    host_path = "/cgroup"
  }

  volume {
    name      = "al2_cgroup"
    host_path = "/sys/fs/cgroup"
  }

  volume {
    name      = "proc"
    host_path = "/proc"
  }

  volume {
    name      = "dev"
    host_path = "/dev"
  }

  container_definitions = jsonencode([{
    name  = "cwagent"
    image = "amazon/cloudwatch-agent:1.247345.36b249270"
    mountPoints = [
      { readOnly = true, containerPath = "/cgroup", sourceVolume = "al1_cgroup" },
      { readOnly = true, containerPath = "/rootfs/cgroup", sourceVolume = "al1_cgroup" },
      { readOnly = true, containerPath = "/rootfs/dev", sourceVolume = "dev" },
      { readOnly = true, containerPath = "/rootfs/proc", sourceVolume = "proc" },
      { readOnly = true, containerPath = "/rootfs/sys/fs/cgroup", sourceVolume = "al2_cgroup" },
      { readOnly = true, containerPath = "/sys/fs/cgroup", sourceVolume = "al2_cgroup" },
    ]
    environment = [
      { name = "USE_DEFAULT_CONFIG", value = "True" }
    ]
    logConfiguration = {
      logDriver = "awslogs",
      options = {
        awslogs-create-group  = "True",
        awslogs-group         = "/ecs/cwagent",
        awslogs-region        = data.aws_region.current.name,
        awslogs-stream-prefix = "cwagent"
      }
    }
  }])
}

resource "aws_ecs_service" "this" {
  name                = "cwagent"
  cluster             = var.cluster_name
  launch_type         = "EC2"
  scheduling_strategy = "DAEMON"
  task_definition     = aws_ecs_task_definition.this.arn
}
