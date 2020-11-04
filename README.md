# terraform-aws-ecs-container-instances

This module is used to create an Auto Scaling Group of ECS container instances. It works with [terraform-aws-ecs-service-pipeline](https://github.com/claranet/terraform-aws-ecs-service-pipeline) for deploying ECS services [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) for deploying new AMIs.

## Overview

* The Auto Scaling Group is created with [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) so a pipeline can optionally be used to deploy new AMIs.
* Lifecycle hooks ensure that instances have joined the ECS cluster before they are put in service.
* Lifecycle hooks ensure that instances have been drained of tasks before they are terminated.
* CloudWatch Agent is started as a daemon service.
* Creates an auto scaling capacity provider.
  * Not compatible with [blue/green deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html#deployment-type-bluegreen-considerations).
  * See [terraform-aws-ecs-service-pipeline](https://github.com/claranet/terraform-aws-ecs-service-pipeline) for an example of a compatible ECS service.

The following diagram shows how we have used this module to handle AMI deployments to ECS container instances in multiple environments. Deployments always roll out to the development environment straight away, but require approval before being promoted to the staging and production environments.

![Diagram](diagram.png?raw=true)

## Creating a pipeline

1. Use this module in one or more environments.
2. Not supplied: Create an S3 bucket to use for AMI manifests and do something like:
  * Use Packer to build custom AMIs and write the manifest to the S3 bucket.
  * Attach a Lambda function to [Amazon ECS-optimized AMI update notifications](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS-AMI-SubscribeTopic.html) and upload a fake Packer manifest to the S3 bucket.
3. Use the `pipeline` module from [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) to create a pipeline.
    * Specify `type=ami`.
    * Pass in the S3 bucket details as the `source_location`.
    * Pass in the `pipeline_target` output from anywhere you used this module.
4. Trigger the pipeline by running Packer or waiting for AMI update notifications.
