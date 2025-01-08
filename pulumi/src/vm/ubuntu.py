import os
import pulumi
import pulumi_kubernetes as k8s


def deploy_ubuntu_vm(config_vm, k8s_provider: k8s.Provider, depends_on: list = []):
    # Extract configuration values from config_vm
    namespace = config_vm.get("namespace", "default")
    instance_name = config_vm.get("instance_name", "ubuntu")
    image_name = config_vm.get("image_name", "docker.io/containercraft/ubuntu:22.04")
    node_port = config_vm.get("node_port", 30590)
    ssh_user = config_vm.get("ssh_user", "kc2")
    ssh_password = config_vm.get("ssh_password", "kc2")
    ssh_pub_key = config_vm.get("ssh_pub_key", "")
    app_name = "kc2"

    # Create Secret `kc2-pubkey` from public key string
    kc2_pubkey_secret = k8s.core.v1.Secret(
        "kc2-pubkey",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="kc2-pubkey",
            namespace=namespace,
        ),
        type="Opaque",
        string_data={
            "key1": ssh_pub_key,
        },
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=depends_on),
    )

    # Define the Service
    ubuntu_ssh_service = k8s.core.v1.Service(
        "ubuntu-ssh",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ubuntu-ssh",
            namespace=namespace,
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            type="NodePort",
            ports=[
                k8s.core.v1.ServicePortArgs(
                    node_port=node_port,
                    port=node_port,
                    protocol="TCP",
                    target_port=22,
                )
            ],
            selector={
                f"{app_name}.ccio.io/instance": instance_name,
            },
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=depends_on),
    )

    # Cloud-init user data for VM configuration
    user_data = f"""#cloud-config
    ssh_pwauth: true
    disable_root: true
    chpasswd:
      list: |
         {ssh_user}:{ssh_password}
      expire: False
    users:
      - name: {ssh_user}
        shell: /bin/bash
        lock_passwd: false
        sudo: ['ALL=(ALL) NOPASSWD:ALL']
        groups: sudo,lxd,libvirt,microk8s,xrdp,docker,ssl-cert
    growpart:
      mode: auto
      devices: ['/']
      ignore_growroot_disabled: true
    package_upgrade: false
    packages:
      - docker.io
    runcmd:
      - "echo H4sIAAAAAAACA7WRwU7DMAyG73mKaHe6dRrTyKsghELibWYhjhy3gBDvTkIXtRJC4oJP8R/ntz/HUTziyeiPTxVBXokv2agb7SZZ6RKYxl0XrRi9Eh5gNYvWe4acje7vtl2/P3S3h65fb3f6X6L13c99I0UosofsGJMgxTJkHTDaFzA6vPkn3pRU3hNcbxLTM7gC4+FohyAqC7E9wWMiCkv2upLfrdvrUsE4AhcFWRXzIwb4i42HEV2trFQg5810av5VacL0LwucGhNSRPedM5E0g2TlbPS6ZQVrOe781mO+/OC5rqfs9v5BuTBkqWxxCEF9AXZkJoMrAgAA | base64 -d | gzip -d | lxd init --preseed"
      - "screenfetch"
    """

    # Cloud-init network data for VM configuration
    network_data = """version: 2
    ethernets:
      enp1s0:
        dhcp4: true
        dhcp6: false
        dhcp-identifier: mac
    """

    # Define the VirtualMachine
    ubuntu_vm = k8s.apiextensions.CustomResource(
        "ubuntu",
        api_version="kubevirt.io/v1",
        kind="VirtualMachine",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=instance_name,
            namespace=namespace,
            labels={
                "app": app_name,
            },
        ),
        spec={
            "running": True,
            "template": {
                "metadata": {
                    "labels": {
                        "app": app_name,
                        f"{app_name}.ccio.io/instance": instance_name,
                    },
                },
                "spec": {
                    "hostname": instance_name,
                    "domain": {
                        "clock": {"utc": {}},
                        "cpu": {
                            "model": "host-passthrough",
                            "dedicatedCpuPlacement": False,
                            "isolateEmulatorThread": False,
                        },
                        "resources": {"limits": {"memory": "4Gi", "cpu": 2}},
                        "devices": {
                            "rng": {},
                            "autoattachPodInterface": False,
                            "autoattachSerialConsole": True,
                            "autoattachGraphicsDevice": True,
                            "networkInterfaceMultiqueue": False,
                            "disks": [
                                {
                                    "name": "containerdisk",
                                    "bootOrder": 1,
                                    "disk": {"bus": "virtio"},
                                },
                                {"name": "cloudinitdisk", "disk": {"bus": "virtio"}},
                            ],
                            "interfaces": [
                                {"name": "enp1s0", "model": "virtio", "bridge": {}}
                            ],
                        },
                        "machine": {"type": "q35"},
                    },
                    "networks": [{"name": "enp1s0", "pod": {}}],
                    "terminationGracePeriodSeconds": 0,
                    "accessCredentials": [
                        {
                            "sshPublicKey": {
                                "source": {
                                    "secret": {
                                        "secretName": kc2_pubkey_secret.metadata["name"]
                                    }
                                },
                                "propagationMethod": {
                                    "qemuGuestAgent": {"users": [ssh_user]}
                                },
                            }
                        }
                    ],
                    "volumes": [
                        {
                            "name": "containerdisk",
                            "containerDisk": {
                                "image": image_name,
                                "imagePullPolicy": "Always",
                            },
                        },
                        {
                            "name": "cloudinitdisk",
                            "cloudInitNoCloud": {
                                "networkData": network_data,
                                "userData": user_data,
                            },
                        },
                    ],
                },
            },
        },
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=depends_on),
    )

    # Export the Service URL and VM name as outputs
    pulumi.export("service_name", ubuntu_ssh_service.metadata["name"])
    pulumi.export("vm_name", ubuntu_vm.metadata["name"])

    return ubuntu_vm, ubuntu_ssh_service
