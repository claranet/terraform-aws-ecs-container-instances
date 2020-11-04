variable "boot_timeout_seconds" {
  description = "The time allowed for instances to boot before giving up."
  type        = number
  # Allow 15 minutes. It normally takes 2 minutes to launch and run the boot script.
  default = 60 * 15
}

variable "cluster_name" {
  type = string
}

variable "drain_timeout_seconds" {
  description = "The time allowed for instances to be drained before giving up."
  type        = number
  # Allow 1 hour. It normally takes several minutes to drain tasks when terminating.
  # CloudFormation custom resources, which are used for draining, have a 1 hour limit
  # so 1 hour is the maximum we can use here. We could use a more complicated
  # CloudFormation wait condition if this limit is a problem.
  default = 60 * 60
}

variable "instance_type" {
  type = string
}

variable "max_size" {
  type = number
}

variable "pipeline_auto_deploy" {
  type = bool
}

variable "pipeline_aws_account_id" {
  type = string
}

variable "pipeline_target_name" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "user_data" {
  type    = string
  default = ""
}

variable "vpc_id" {
  type = string
}
