This module handles "draining" when an instance is being terminated.

The auto scaling group has a lifecycle action for when instances are terminated. This will trigger a CloudWatch Event rule, which sends the event to an SQS queue. This queue's messages are processed by a Lambda function.

The Lambda function checks whether any ECS tasks are on the instance. If there are tasks, it will tell ECS to drain the instance. ECS will then move these tasks onto another instance. This can take a while, so the Lambda function puts the event back onto the queue with a delay.

After the delay, the Lambda function will process the message again. If the instance still has tasks, it puts the message on the queue to check again later, repeating as many times as necessary.

When there are no tasks, the Lambda function completes the lifecycle action and allows the auto scaling group to terminate the instance.

```
+-----+                                            +-----+
| ASG |-- Teminating:Wait --> CloudWatch Event --> | SQS | <-- Resend message --+
+-----+                                            +-----+                      |
   ^                                                  |                         |
   |                                                  v                         | 
   |                                              +--------+                    |
   +--------- Teminating:Proceed <-- NO TASKS? -- | Lambda |-- HAS TASKS? ------+
                                                  +--------+
                                                      |
                                                      |
                                                STATUS IS NOT
                                                  DRAINING?
                                                      |
                                                      |
                                                Update status
                                                      |
                                                      v
                                                   +-----+
                                                   | ECS |
                                                   +-----+
```
