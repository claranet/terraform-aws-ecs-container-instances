from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2
from diagrams.aws.devtools import Codebuild, Codepipeline
from diagrams.aws.management import AutoScaling, Cloudformation
from diagrams.aws.storage import S3
from diagrams.onprem.client import User
from diagrams.onprem.vcs import Github


def green(color="forestgreen", style="solid"):
    return Edge(color=color, style=style)


def red(color="firebrick", style="solid"):
    return Edge(color=color, style=style)


with Diagram("ECS Container Instances Pipeline", filename="diagram", outformat="png"):

    with Cluster("Management AWS Account"):

        codebuild = Codebuild("CodeBuild\nPacker AMI")

        with Cluster("S3-Source Module"):
            s3 = S3("S3 Object\nami.zip")

        with Cluster("Pipeline Module"):
            pipeline_source = Codepipeline("S3 Source\nami.zip")
            pipeline_dev = Codepipeline("Deploy to\nDev")
            pipeline_approval_staging = User("Manual\nApproval")
            pipeline_staging = Codepipeline("Deploy to\nStaging")
            pipeline_approval_prod = User("Manual\nApproval")
            pipeline_prod = Codepipeline("Deploy to\nProd")

    with Cluster("Development AWS Account"):
        with Cluster("Container Instances Module"):
            with Cluster("ASG Module"):
                cfn_dev = Cloudformation("CloudFormation\nStack")
                with Cluster("CloudFormation Resources"):
                    asg_dev = AutoScaling("Auto Scaling\nGroup")
                    ec2_dev = EC2("EC2 Instances")

    with Cluster("Staging AWS Account"):
        with Cluster("Container Instances Module"):
            with Cluster("ASG Module"):
                cfn_staging = Cloudformation("CloudFormation\nStack")
                with Cluster("CloudFormation Resources"):
                    asg_staging = AutoScaling("Auto Scaling\nGroup")
                    ec2_staging = EC2("EC2 Instances")

    with Cluster("Production AWS Account"):
        with Cluster("Container Instances Module"):
            with Cluster("ASG Module"):
                cfn_prod = Cloudformation("CloudFormation\nStack")
                with Cluster("CloudFormation Resources"):
                    asg_prod = AutoScaling("Auto Scaling\nGroup")
                    ec2_prod = EC2("EC2 Instances")

    codebuild >> s3 >> pipeline_source >> pipeline_dev >> pipeline_approval_staging >> pipeline_staging >> pipeline_approval_prod >> pipeline_prod
    pipeline_dev >> red() >> cfn_dev >> red() >> asg_dev >> red() >> ec2_dev
    ec2_staging << red() << asg_staging << red() << cfn_staging << red() << pipeline_staging
    pipeline_prod >> red() >> cfn_prod >> red() >> asg_prod >> red() >> ec2_prod
