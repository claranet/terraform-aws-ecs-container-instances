# terraform-aws-ecs-container-instances

This module is used to create an Auto Scaling Group of ECS container instances. It works with [terraform-aws-ecs-service-pipeline](https://github.com/claranet/terraform-aws-ecs-service-pipeline) for deploying ECS services on top of these container instances, and [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) for deploying new AMIs to these container instances.

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

The following diagram shows at a higher level how we have used this module in conjunction with the [terraform-aws-ecs-service-pipeline](https://github.com/claranet/terraform-aws-ecs-service-pipeline) module to provide a complete ECS-on-EC2 solution.

![Diagram](diagram-with-services.png?raw=true)

## Creating a pipeline

1. Use this module in one or more environments.
2. Use the `s3-source` module from [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) to create an S3 bucket for manifests of AMIs to be deployed by the pipeline.
    * Or create the S3 bucket yourself. You'll just need to build the simple `source_location` object to pass into the `pipeline` module.
3. Use the `pipeline` module from [terraform-aws-asg-pipeline](https://github.com/claranet/terraform-aws-asg-pipeline) to create a pipeline.
    * Specify `type=ami`.
    * Pass in the S3 source details as the `source_location`.
    * Pass in the `pipeline_target` output from anywhere you used this module.
4. Not included: Write AMI manifests to the S3 bucket location to trigger the pipeline.
    * Use Packer to build a custom AMI and upload a zipped manifest to the S3 bucket.
    * Attach a Lambda function to [Amazon ECS-optimized AMI update notifications](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS-AMI-SubscribeTopic.html) and upload a fake Packer manifest to the S3 bucket, to roll out the new AMI automatically when AWS releases them.
