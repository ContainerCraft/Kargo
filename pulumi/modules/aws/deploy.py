# src/aws/deploy.py
# Description: generic boilerplate code not currently active in the project.
# This code is provided as a reference for future implementation.
# Key features include utilization of generate_compliance_tags, generate_compliance_labels, and generate_compliance_annotations functions from src/compliance/utils.py.

import pulumi
from pulumi import ResourceOptions
import pulumi_aws as aws
import pulumi_eks as eks
import pulumi_kubernetes as k8s

# Global Pulumi settings
stack_tags = {
    "project": pulumi.get_project(),
    "stack": pulumi.get_stack(),
    "owner": "pulumi-user",
}

stack_labels = {
    "environment": "testing",
}

pulumi.runtime.set_all_project_tags(stack_tags)
pulumi.runtime.set_all_project_labels(stack_labels)

# AWS S3 Bucket with global tags
s3_bucket = aws.s3.Bucket("nginxStorageBucket",
    tags={
        **stack_tags,
        "Name": "nginxStorageBucket",
        "Environment": "Dev",
    }
)

# AWS EKS Cluster with global tags
eks_cluster = eks.Cluster("exampleCluster",
    tags={
        **stack_tags,
        "Name": "exampleCluster",
        "Environment": "Dev",
    }
)

# Kubernetes Persistent Volume
persistent_volume = k8s.core.v1.PersistentVolume("nginxPv",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="nginx-pv",
        labels={
            **stack_labels,
            "type": "local",
        }
    ),
    spec=k8s.core.v1.PersistentVolumeSpecArgs(
        capacity={"storage": "1Gi"},
        access_modes=["ReadWriteOnce"],
        aws_elastic_block_store=k8s.core.v1.AWSElasticBlockStoreVolumeSourceArgs(
            volume_id=s3_bucket.id.apply(lambda id: f"aws://{aws.region}/{id}"),
            fs_type="ext4",
        ),
    ),
    opts=ResourceOptions(parent=eks_cluster)
)

# Kubernetes Persistent Volume Claim
persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim("nginxPvc",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="nginx-pvc",
        labels=stack_labels,
    ),
    spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteOnce"],
        resources=k8s.core.v1.ResourceRequirementsArgs(
            requests={"storage": "1Gi"},
        ),
    ),
    opts=ResourceOptions(parent=eks_cluster)
)

# Kubernetes Nginx Deployment with Persistent Storage
nginx_deployment = k8s.apps.v1.Deployment("nginxDeployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="nginx-deployment",
        labels={
            **stack_labels,
            "app": "nginx",
        }
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={
                "app": "nginx",
            }
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={
                    **stack_labels,
                    "app": "nginx",
                }
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="nginx",
                        image="nginx:1.14.2",
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=80)],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name="nginx-storage",
                                mount_path="/usr/share/nginx/html",
                            )
                        ],
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name="nginx-storage",
                        persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                            claim_name=persistent_volume_claim.metadata.name,
                        )
                    )
                ]
            )
        ),
    ),
    opts=ResourceOptions(parent=eks_cluster)
)

pulumi.export("s3BucketName", s3_bucket.bucket)
pulumi.export("eksClusterName", eks_cluster.core.apply(lambda core: core.endpoint))
