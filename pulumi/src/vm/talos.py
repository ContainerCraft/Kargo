import pulumi
import pulumi_kubernetes as k8s

def deploy_talos_cluster(
        config_talos: dict,
        k8s_provider: k8s.Provider,
        depends_on: pulumi.Output[list],
        parent
    ):
    """
    Deploy the Talos controlplane and worker VirtualMachinePools based on the provided configuration.
    """

    # Get configurations for controlplane and workers, with defaults applied
    controlplane_config = get_talos_config(config_talos.get("controlplane", {}), "controlplane")
    worker_config = get_talos_config(config_talos.get("workers", {}), "workers")

    # Apply the running flag to both configurations
    controlplane_config["running"] = config_talos.get("running", True)
    worker_config["running"] = config_talos.get("running", True)

    # Deploy the Talos controlplane
    controlplane_vm_pool = deploy_talos_cluster_controlplane(
        config_vm=controlplane_config,
        k8s_provider=k8s_provider,
        depends_on=depends_on,
        parent=parent
    )

    # Deploy the Talos workers (if replicas > 0)
    worker_vm_pool = None
    if worker_config["replicas"] > 0:
        worker_vm_pool = deploy_talos_cluster_workers(
            config_vm=worker_config,
            k8s_provider=k8s_provider,
            depends_on=depends_on,
            parent=parent
        )

    return controlplane_vm_pool, worker_vm_pool

def get_talos_config(
        config_talos_cluster: dict,
        node_type: str
    ) -> dict:
    """
    Generate the Talos cluster configuration by merging common default values with node-specific config.
    """
    # Common default configuration for both controlplane and workers
    common_talos_defaults = {
        "namespace": "default",
        "image": config_talos_cluster.get("image", "docker.io/containercraft/talos:1.7.6"),
        "network_name": "br0",  # Default network
        "running": True  # Default running state
    }

    # Set vm_pool_name for controlplane and workers
    vm_pool_name = f"kargo-dev-{node_type}"

    # Handle controlplane configuration
    if node_type == "controlplane":
        controlplane_replicas = 1  # Default to single
        controlplane_config = config_talos_cluster.get('replicas', 'single')

        if controlplane_config == 'single':
            controlplane_replicas = 1
        elif controlplane_config == 'ha':
            controlplane_replicas = 3
        else:
            pulumi.log.error(f"Unrecognized controlplane replica config. Expected 'single' or 'ha', got: {controlplane_config}")
            raise ValueError(f"Invalid controlplane config: {controlplane_config}")

        # Controlplane-specific defaults and configuration overrides
        controlplane_defaults = {
            "replicas": controlplane_replicas,
            "cpu_cores": config_talos_cluster.get("cpu_cores", 1),
            "memory_size": config_talos_cluster.get("memory_size", "2"),  # Memory in GiB
            "root_disk_size": config_talos_cluster.get("root_disk_size", "32"),  # Root disk size in GiB
            "empty_disk_size": config_talos_cluster.get("empty_disk_size", "0"),  # Empty disk size in GiB
            "vm_pool_name": vm_pool_name
        }
        return {**common_talos_defaults, **controlplane_defaults}

    # Handle worker configuration
    elif node_type == "workers":
        worker_defaults = {
            "replicas": config_talos_cluster.get("replicas", 0),  # Worker replicas
            "cpu_cores": config_talos_cluster.get("cpu_cores", 2),  # Worker CPU cores
            "memory_size": config_talos_cluster.get("memory_size", "2"),  # Worker memory in GiB
            "root_disk_size": config_talos_cluster.get("root_disk_size", "32"),  # Root disk size in GiB
            "empty_disk_size": config_talos_cluster.get("empty_disk_size", "16"),  # Empty disk size in GiB
            "vm_pool_name": vm_pool_name
        }
        return {**common_talos_defaults, **worker_defaults}

    else:
        raise ValueError(f"Unsupported node type: {node_type}")

def deploy_talos_cluster_controlplane(
        config_vm,
        k8s_provider: k8s.Provider,
        depends_on: pulumi.Output[list],
        parent
    ):
    """
    Deploy the Talos cluster controlplane with specific configuration.
    """
    vm_pool_spec = generate_talos_vmpool_spec(
        vm_pool_name=config_vm["vm_pool_name"],
        namespace=config_vm["namespace"],
        replicas=config_vm["replicas"],  # Controlplane replicas
        cpu_cores=config_vm["cpu_cores"],
        memory_size=config_vm["memory_size"],
        root_disk_size=config_vm["root_disk_size"],
        empty_disk_size=config_vm["empty_disk_size"],
        image_address=config_vm["image"],
        network_name=config_vm["network_name"],
        running=config_vm["running"]
    )

    controlplane_vm_pool = k8s.apiextensions.CustomResource(
        f"{config_vm['vm_pool_name']}",
        api_version="pool.kubevirt.io/v1alpha1",
        kind="VirtualMachinePool",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=f"{config_vm['vm_pool_name']}",
            namespace=config_vm["namespace"],
        ),
        spec=vm_pool_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            #depends_on=depends_on,
            parent=parent
        )
    )

    return controlplane_vm_pool

def deploy_talos_cluster_workers(
        config_vm,
        k8s_provider: k8s.Provider,
        depends_on,
        parent
    ):
    """
    Deploy the Talos workers with their specific configuration.
    """
    if config_vm["replicas"] > 0:
        worker_vm_pool_spec = generate_talos_vmpool_spec(
            vm_pool_name=config_vm["vm_pool_name"],
            namespace=config_vm["namespace"],
            replicas=config_vm["replicas"],
            cpu_cores=config_vm["cpu_cores"],
            memory_size=config_vm["memory_size"],
            root_disk_size=config_vm["root_disk_size"],
            empty_disk_size=config_vm["empty_disk_size"],
            image_address=config_vm["image"],
            network_name=config_vm["network_name"],
            running=config_vm["running"]
        )

        worker_vm_pool = k8s.apiextensions.CustomResource(
            f"{config_vm['vm_pool_name']}-workers",
            api_version="pool.kubevirt.io/v1alpha1",
            kind="VirtualMachinePool",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"{config_vm['vm_pool_name']}",
                namespace=config_vm["namespace"],
            ),
            spec=worker_vm_pool_spec,
            opts=pulumi.ResourceOptions(
                provider=k8s_provider,
                #depends_on=depends_on,
                parent=parent
            )
        )
    else:
        worker_vm_pool = None

    return worker_vm_pool

def generate_talos_vmpool_spec(
        vm_pool_name: str,
        namespace: str,
        replicas: int,
        cpu_cores: int,
        memory_size: str,
        root_disk_size: str,
        empty_disk_size: str,
        image_address: str,
        network_name: str,
        running: bool
    ) -> dict:
    """
    Generate the VirtualMachinePool spec for Talos VMs.
    """
    # Ensure the correct image is passed here
    docker_image_address = f"docker://{image_address}"

    # Initialize the spec with a root disk data volume template
    spec = {
        "replicas": replicas,
        "selector": {
            "matchLabels": {
                "kubevirt.io/vmpool": vm_pool_name
            }
        },
        "virtualMachineTemplate": {
            "metadata": {
                "labels": {
                    "kubevirt.io/vmpool": vm_pool_name
                }
            },
            "spec": {
                "running": running,
                "template": {
                    "metadata": {
                        "labels": {
                            "kubevirt.io/vmpool": vm_pool_name
                        }
                    },
                    "spec": {
                        "networks": [
                            {
                                "name": "eth0",
                                "multus": {
                                    "networkName": network_name
                                }
                            }
                        ],
                        "domain": {
                            "cpu": {
                                "cores": cpu_cores  # Use configured CPU cores
                            },
                            "resources": {
                                "requests": {
                                    "memory": f"{memory_size}Gi"  # Use configured memory size
                                }
                            },
                            "devices": {
                                "disks": [
                                    {
                                        "name": "talos-root-disk",
                                        "bootOrder": 1,
                                        "disk": {
                                            "bus": "virtio"
                                        }
                                    }
                                ],
                                "interfaces": [
                                    {
                                        "name": "eth0",
                                        "bridge": {}
                                    }
                                ]
                            }
                        },
                        "volumes": [
                            {
                                "name": "talos-root-disk",
                                "dataVolume": {
                                    "name": f"{vm_pool_name}-root-dv"
                                }
                            }
                        ]
                    }
                },
                "dataVolumeTemplates": [
                    {
                        "metadata": {
                            "name": f"{vm_pool_name}-root-dv"
                        },
                        "spec": {
                            "storage": {
                                "accessModes": ["ReadWriteOnce"],
                                "resources": {
                                    "requests": {
                                        "storage": f"{root_disk_size}Gi"  # Use configured root disk size
                                    }
                                }
                            },
                            "source": {
                                "registry": {
                                    "url": docker_image_address,  # Ensure the correct image URL is propagated here
                                }
                            }
                        }
                    }
                ]
            }
        }
    }

    # If the empty disk size is greater than 0, add the empty disk to the spec
    if int(empty_disk_size) > 0:
        spec["virtualMachineTemplate"]["spec"]["template"]["spec"]["domain"]["devices"]["disks"].append(
            {
                "name": "talos-empty-disk",
                "disk": {
                    "bus": "virtio"
                }
            }
        )

        spec["virtualMachineTemplate"]["spec"]["template"]["spec"]["volumes"].append(
            {
                "name": "talos-empty-disk",
                "dataVolume": {
                    "name": f"{vm_pool_name}-empty-dv"
                }
            }
        )

        # Append the empty disk data volume template
        spec["virtualMachineTemplate"]["spec"]["dataVolumeTemplates"].append(
            {
                "metadata": {
                    "name": f"{vm_pool_name}-empty-dv"
                },
                "spec": {
                    "storage": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {
                            "requests": {
                                "storage": f"{empty_disk_size}Gi"  # Use configured empty disk size
                            }
                        }
                    },
                    "source": {
                        "blank": {}
                    }
                }
            }
        )

    return spec
