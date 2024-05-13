# Kargo FAQ

## What is Kargo?

Kargo is an idea. First things first, Kargo is not a specific technology or product. Kargo is a platform assembled from many technologies, with the idea of delivering the easiest and most collaborative "at home" cloud as a service.

Specific tooling and product choices always favor real enterprise OSS product selection and implementation. If you are running Kargo, you are running real enterprise cloud technology!

Over time, the tooling and product choices will evolve, but the idea of Kargo will remain the same. Deliver containers, VMs, networking, storage, and compute as a service for fun and friends!

## What is Talos, and why use it?

Talos is a modern operating system for Kubernetes. It is designed to be immutable, minimal, and secure. Talos is a perfect fit for Kargo because it is designed to be a Kubernetes node, and it is designed to be managed by Kubernetes.

Key features of Talos result in extremely low user management overhead, and all configuration is declarative. Other than booting Talos for the first install and hitting the power button, there is no imperative or "step by step" configuration required. Even if you want to wipe your cluster and start over, there is an API for that! Relative to k3s, microk8s, or other common "at home" kubernetes distributions, Talos does not require you to manage the OS, learn systemd, networkd, or any other Linux system management tools.

Finally, Talos is managed declaratively. This means that you can manage your entire cluster with GitOps, and you can use the same tools and workflows that you use for your applications to manage your infrastructure and even bare metal OS.

## What about Proxmox?

Proxmox is a legacy virtualization platform that is heavily dependent on many manual and imperative management demands.

Kargo schedules VMs with a kubernetes technology called KubeVirt. Proxmox and KubeVirt are both powered by the same linux KVM hypervisor underneath. If you like Proxmox, we think you will LOVE Kargo powered by KubeVirt!

If you already run Proxmox at home, you can provision a new 1 or 3 node Talos k8s cluster to try Kargo yourself without committing to wipe your hardware and convert it without knowing if you like it first.

Most importantly, the Proxmox community is limited in their velocity and reach when building, sharing, distributing, and reproducing projects built on top of Proxmox. Kargo brings the sharable and reproducible power of applications and infrastructure to the Homelab community. Build and share with friends, and make new friends along the way. We are a community focused project dedicated to technologies that empower the growth and innovation of our community more than product or technology specific attachment.

Use the tools that help you learn and grow your skills and achieve your goals. The Kargo is not a tribal all or nothing culture. Let's learn together.

## What about K3s?

There are many other ways to run Kubernetes. After experiencing them in the field and at home, we have discovered that Talos is currently the only game in town which does not demand a steep learning curve if you are new to the Kubernetes space. Other distributions require specialized OS selection and prerequisites. Talos brings everything you need to run Kubernetes in the first boot, and it can all be managed from a single file on your local Laptop or Desktop of choice. We will never tell you to 'ssh to the node and run this command' or 'install these packages'.

We believe that host management and maintenance is a solved problem, the value in a platform comes from what it can do, not what it is built on. With Talos, you can focus on doing amazing things with your platform and largely ignore having to manage the platform itself. Your homelab should not be a second job, it should be a fun and rewarding hobby that inspires you to do new and creative things!

## How do I reach my VMs, do I need weird Kubernetes port-forwarding or nodeport services?

The default networking scheme for your first Kargo VMs will fallback to a simple interface attached to your host's primary interface network bridge. This means that your VMs will be accessible on your local network, and you can reach them with the same tools and workflows that you use to reach your host machine. You can use SSH, RDP, VNC, or any other protocol that you would use to reach a physical machine on your network just like you would with conventional hypervisors like VMWare and Proxmox.

Because we are using KubeVirt in Kubernetes with Multus however, you can also grow into GitOps network configuration to create vlans, VPNs, proxies, service meshes, api gateways, and many other compelling network topologies and configurations. Using kubernetes services like ngrok, or inlets, we can even assign public cloud IP addresses from the likes of Digital Ocean, AWS, or GCP to your kubernetes services and virtual machines running behind a completely closed firewall!

Most Kargo users do *not* do any `kubectl port-forward` or `kubectl expose` commands to reach their VMs. Simply let your LAN DHCP server assign an IP to your VM, or assign a static IP in the VM's Kubevirt manifest. Everything will be familiar after that with this approach.

The sky is the limit but you can start at the ground floor and be perfectly successful with just the basics if that is what you want!

## Do I have to track the kubernetes admin kubeconfig?

Kargo is kubernetes based. You will have a kubeconfig to keep track of. This will not be the only way to authenticate and operate your cluster however! There are tools like OpenUnison to make your daily platform usage easier and much more convenient.

Using offerings like Pulumi ESC, and Github Codespaces, your entire homelab can be completely managed and developed from a web browser. A chromebook or a tablet can be your primary ops workstation! Even the samsung dex 'desktop on android' experience can deliver everything required to manage your homelab.

As a cloud native homelab platform, Kargo will teach you how to relieve most of the fatigue commonly felt as a barrier to entry in the kubernetes world. If you feel like something is harder than it should be, it probably is, and we are here to help you find a better way!
