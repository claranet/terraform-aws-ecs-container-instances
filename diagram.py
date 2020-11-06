from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, ECR, ECS, Compute
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

with Diagram("ECS Service and Container Instances Pipelines", filename="diagram-with-services", outformat="png"):

    github = Github("GitHub Actions\nImage Build")

    with Cluster("Management AWS Account"):

        codebuild = Codebuild("CodeBuild\nPacker AMI")

        with Cluster("Container Instances Pipeline Module"):
            asg_pipeline_dev = Codepipeline("Deploy to\nDev")
            asg_pipeline_staging = Codepipeline("Deploy to\nStaging")
            asg_pipeline_prod = Codepipeline("Deploy to\nProd")

        with Cluster("Service Pipeline Module"):
            ecs_pipeline_dev = Codepipeline("Deploy to\nDev")
            ecs_pipeline_staging = Codepipeline("Deploy to\nStaging")
            ecs_pipeline_prod = Codepipeline("Deploy to\nProd")

    with Cluster("Development AWS Account"):
        with Cluster("Container Instances Module"):
            asg_dev = AutoScaling("Container Instances")
        with Cluster("Service Module"):
            ecs_dev = ECS("ECS Service")

    with Cluster("Staging AWS Account"):
        with Cluster("Container Instances Module"):
            asg_staging = AutoScaling("Container Instances")
        with Cluster("Service Module"):
            ecs_staging = ECS("ECS Service")

    with Cluster("Production AWS Account"):
        with Cluster("Container Instances Module"):
            asg_prod = AutoScaling("Container Instances")
        with Cluster("Service Module"):
            ecs_prod = ECS("ECS Service")

    (
        codebuild
        >> asg_pipeline_dev
        >> asg_pipeline_staging
        >> asg_pipeline_prod
    )

    (
        github
        >> ecs_pipeline_dev
        >> ecs_pipeline_staging
        >> ecs_pipeline_prod
    )

    if 2 > 1:
        ecs_dev >> green(style="dashed") >> asg_dev
    else:
        asg_dev << green(style="dashed") << ecs_dev
    if 2 > 1:
        asg_pipeline_dev >> red() >> asg_dev
        ecs_pipeline_dev >> green() >> ecs_dev
    else:
        asg_dev << red() << asg_pipeline_dev
        ecs_dev << green() << ecs_pipeline_dev

    if 2 > 1:
        ecs_staging >> green(style="dashed") >> asg_staging
    else:
        asg_staging << green(style="dashed") << ecs_staging
    if 2 < 1:
        asg_pipeline_staging >> red() >> asg_staging
        ecs_pipeline_staging >> green() >> ecs_staging
    else:
        asg_staging << red() << asg_pipeline_staging
        ecs_staging << green() << ecs_pipeline_staging

    if 2 > 1:
        ecs_prod >> green(style="dashed") >> asg_prod
    else:
        asg_prod << green(style="dashed") << ecs_prod
    if 2 > 1:
        ecs_pipeline_prod >> green() >> ecs_prod
        asg_pipeline_prod >> red() >> asg_prod
    else:
        ecs_prod << green() << ecs_pipeline_prod
        asg_prod << red() << asg_pipeline_prod
