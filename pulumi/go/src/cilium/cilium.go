package cilium

import (
	"fmt"
	"log"
	"os"

	"helm.sh/helm/v3/pkg/action"
	"helm.sh/helm/v3/pkg/chart/loader"
	"helm.sh/helm/v3/pkg/cli"
)

func deployHelm(
	releaseName,
	kubernetesDistrubition,
	projectName,
	kubernetesEndpointServiceAddress,
	namespace,
	version,
	l2BridgeName,
	l2Announcements string) {

	// Call upon the getHelmValues function to get the values for the Helm chart.
	helmValues, err := getHelmValues(kubernetesDistrubition, projectName, kubernetesEndpointServiceAddress)
	if err != nil {
		log.Fatalln("Could Not Retrieve Helm Values")
	}

	var (
		chartName = "cilium/cilium"
	)

	settings := cli.New()

	config := new(action.Configuration)

	if err := config.Init(settings.RESTClientGetter(), namespace, os.Getenv("HELM_DRIVER"), log.Printf); err != nil {
		log.Printf("%+v", err)
	}

	client := action.NewInstall(config)

	client.Namespace = namespace
	client.ReleaseName = releaseName

	if version == "" {
		client.Version = ""
	} else {
		client.Version = version
	}

	client.Version = version

	ch, err := client.LocateChart(chartName, settings)
	if err != nil {
		log.Println(err)
	}

	chart, err := loader.Load(ch)
	if err != nil {
		log.Println(err)
	}

	release, err := client.Run(chart, helmValues)
	if err != nil {
		log.Println(err)
	}

	fmt.Println(release)

}

func getHelmValues(kubernetesDistrubition, projectName, kubernetesEndpointServiceAddress string) (map[string]interface{}, map[string]interface{}) {
	kubernetesDistrubition = ""
	projectName = ""
	kubernetesDistrubition = ""

	commonValues := map[string]interface{}{
		"set": "kubeProxyReplacement=strict,encryption.enabled=true,encryption.type=wireguard,l7Proxy=false,routingMode=tunnel,tunnelProtocol=vxlan,image.pullPolicy=ifNotPresent,l2announcements.enabled=true,hostServices.enabled=true,externalIPs.enabled=true,gatewayAPI.enabled=true,hubble.enabled=true,hubble.relay.enabled=true,hubble.ui.enabled=true,ipam.mode=kubernetes,nodePort.enabled=true,hostPort.enabled=true,operator.replicas=1,serviceAccounts.cilium.name=cilium,serviceAccounts.operator.name=cilium-operator",
	}

	if kubernetesDistrubition == "kind" {
		m := map[string]interface{}{"set": "k8sServiceHost=changedvalue,k8sServicePort=6443"}
		m["k8sServiceHost"] = kubernetesEndpointServiceAddress

		return m, commonValues

	} else if kubernetesDistrubition == "talos" {
		m := map[string]interface{}{"set": "autoDirectNodeRoutes=true,containerRuntime.integration=containerd,devices=br+ bond+ thunderbolt+,enableRuntimeDeviceDetection=true,endpointRoutes.enabled=true,bpf.masquerade=true,localRedirectPolicy=true,loadBalancer.algorithm=maglev,loadBalancer.mode=dsr,cgroup.autoMount.enabled=false,hostRoot=/sys/fs/cgroup,routingMode=native,ipv4NativeRoutingCIDR=10.244.0.0/16,k8sServicePort=7445,tunnelProtocol=vxlan,k8sServiceHost=127.0.0.1,kubeProxyReplacement=true,image.pullPolicy=ifNotPresent,hostServices.enabled=false,externalIPs.enabled=true,gatewayAPI.enabled=false,nodePort=true,hostPort=true,rollOutCiliumPods=true,operator.replicas=1,operator.rollOutPods=true,cni.install=true,cni.exclusive=false,securitycontext.capabilities.ciliumAgent=nil,securityContext.capabilities.cleanCiliumState=nil"}
		m["securityContext.capabilities.ciliumAgent"] = []string{"CHOWN", "KILL", "NET_ADMIN", "NET_RAW", "IPC_LOCK", "SYS_ADMIN", "SYS_RESOURCE", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"}
		m["securityContext.capabilities.cleanCiliumState"] = []string{"NET_ADMIN", "SYS_ADMIN", "SYS_RESOURCE"}

		return m, commonValues
	} else {
		log.Fatalln("Unsupported Kubernetes distribution: %q", kubernetesDistrubition)
	}

	return nil, nil
}
