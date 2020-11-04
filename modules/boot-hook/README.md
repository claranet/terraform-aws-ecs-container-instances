This module handles the lifecycle hook when an instance is being launched.

The auto scaling group has a lifecycle action for when instances are launched. This will trigger a CloudWatch Event rule, which invokes a Lambda function, which waits until the instance has joined the ECS cluster and then completes the lifecycle action.
