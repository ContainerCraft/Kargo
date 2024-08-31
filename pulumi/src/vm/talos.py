import pulumi
import pulumi_kubernetes as k8s

def deploy_talos_controlplane(
        config_vm,
        k8s_provider: k8s.Provider,
        depends_on: list = []
    ):

    # Generate the VirtualMachinePool spec using the provided config
    vm_pool_spec = generate_talos_vm_pool_spec(
        vm_pool_name=config_vm["vm_pool_name"],
        namespace=config_vm["namespace"],
        replicas=config_vm["replicas"],
        cpu_cores=config_vm["cpu_cores"],
        memory_size=config_vm["memory_size"],
        root_disk_size=config_vm["root_disk_size"],
        empty_disk_size=config_vm["empty_disk_size"],
        image_name=config_vm["image_name"],
        network_name=config_vm["network_name"]
    )

    # Create the VirtualMachinePool resource
    vm_pool = k8s.apiextensions.CustomResource(
        config_vm["vm_pool_name"],
        api_version="pool.kubevirt.io/v1alpha1",
        kind="VirtualMachinePool",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=config_vm["vm_pool_name"],
            namespace=config_vm["namespace"],
        ),
        spec=vm_pool_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on
        )
    )

    return vm_pool

def generate_talos_vm_pool_spec(
        vm_pool_name: str,
        namespace: str,
        replicas: int,
        cpu_cores: int,
        memory_size: str,
        root_disk_size: str,
        empty_disk_size: str,
        image_name: str,
        network_name: str
    ) -> dict:
    """
    Generate the VirtualMachinePool spec for Talos VMs.
    This function can be used for both control plane and worker node VM pools.
    """
    return {
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
                "running": True,
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
                                "cores": cpu_cores
                            },
                            "resources": {
                                "requests": {
                                    "memory": memory_size
                                }
                            },
                            "devices": {
                                "interfaces": [
                                    {
                                        "name": "eth0",
                                        "bridge": {}
                                    }
                                ],
                                "disks": [
                                    {
                                        "name": "talos-root-disk",
                                        "bootOrder": 1,
                                        "disk": {
                                            "bus": "virtio"
                                        }
                                    },
                                    {
                                        "name": "talos-empty-disk",
                                        "disk": {
                                            "bus": "virtio"
                                        }
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
                            },
                            {
                                "name": "talos-empty-disk",
                                "dataVolume": {
                                    "name": f"{vm_pool_name}-empty-dv"
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
                                        "storage": root_disk_size
                                    }
                                }
                            },
                            "source": {
                                "registry": {
                                    "url": image_name
                                }
                            }
                        }
                    },
                    {
                        "metadata": {
                            "name": f"{vm_pool_name}-empty-dv"
                        },
                        "spec": {
                            "storage": {
                                "accessModes": ["ReadWriteOnce"],
                                "resources": {
                                    "requests": {
                                        "storage": empty_disk_size
                                    }
                                }
                            },
                            "source": {
                                "blank": {}
                            }
                        }
                    }
                ]
            }
        }
    }
