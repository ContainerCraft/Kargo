# Kargo Prometheus Deployment

Prometheus is a powerful monitoring system. This program will deploy the full Kube-Prometheus-Stack chart, including Prometheus, AlertManager, and Grafana - https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack

If you have deployed OpenUnison to your stack, all three apps will be configured with SSO and secure access via OpenUnison. Otherwise, you can portforward to the appropriate service. See **_Access_** section after **_Configuration_**.

# Configuration

To enable the Prom Kube Stack deployments:

```
$ pulumi config set prometheus.enabled true
```

If OpenUnison is configured, SSO will automatically be configured to work with OpenUnison

# Access

## With OpenUnison Enabled

Login to your OpenUnison portal and you will see badges for Prometheus, Grafana, and AlertManager.

## Without OpenUnison Enabled

## Prometheus

```
$ kubectl port-forward svc/prometheus -n monitoring 9090:9090
```

## Grafana

```
kubectl port-forward svc/grafana -n monitoring 8080:80
```

Use the username `admin` and the password `prom-operator`

## AlertManager

```
$ kubectl port-forward svc/alertmanager -n monitoring 9093:9093
```
