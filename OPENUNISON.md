# OpenUnison for Cluster Access

# Dependencies

1. Ingress NGINX (not included for now)
2. DNS suffix

# Setup

Enable Cert-Manager

```
pulumi config set cert_manager.enabled true
```

Set a domain suffix

```
pulumi config set openunison.dns_suffix kargo.tremolo.dev
```

Set a `ClusterIssuer`

```
pulumi config set openunison.cluster_issuer cluster-selfsigned-issuer-ca
```
