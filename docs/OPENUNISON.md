# OpenUnison for Cluster Access

# Dependencies

1. Ingress NGINX (not included for now)

For MVP Ingress NGINX is required - https://kubernetes.github.io/ingress-nginx/deploy/

If you don't have a load balancer setup you'll want to deploy as a `DaemonSet` and update the `Deployment` or `DaemonSet` to listen on `hostPort`. First, patch the `ingress-nginx` `Namespace` to allow privileged pods:

```sh
kubectl patch namespace ingress-nginx -p '{"metadata":{"labels":{"pod-security.kubernetes.io/enforce":"privileged"}}}'
```

Next, patch the `DaimonSet` / `Deployment` to listen on 80 and 443:

```sh
kubectl patch deployments ingress-nginx-controller -n ingress-nginx -p '{"spec":{"template":{"spec":{"containers":[{"name":"controller","ports":[{"containerPort":80,"hostPort":80,"protocol":"TCP"},{"containerPort":443,"hostPort":443,"protocol":"TCP"}]}]}}}}'
```

2. DNS suffix

OpenUnison requires a minimum of three host names. More if deploying aditional platform management apps. For this reason, you'll need to create a DNS wildcard for a domain suffix to point to your nodes/load balancer. For instance, in the below examples a wildcard of \*.kargo.tremolo.dev was setup with an A record for my lab hosts. For a full explination, see - https://openunison.github.io/deployauth/#host-names-and-networking

3. GitHub Deployment

Before deploying OpenUnison, you'll need to create an orgnaization on GitHub. This is 100% free. Once you have created an organization, you can setup an OAuth App. See https://openunison.github.io/deployauth/#github for instructions. Your redirect URL will be `https://k8sou.DNS Suffix/auth/github`. You should also create a Team that you'll use authorizing access to your lab. Keep your `client_id` and `client_secret`.

# Setup

Enable Cert-Manager

OpenUnison requires TLS. Instead of the self-signed certs that OpenUnison uses by default, use the integrated Cert-Manager that comes with HomeLab. If you don't have an existing `ClusterIssuer` you want to use, you can use HomeLab's.

```
pulumi config set cert_manager.enabled true
```

Set a `ClusterIssuer`

```
pulumi config set openunison.cluster_issuer cluster-selfsigned-issuer-ca
```

Set a domain suffix

```
pulumi config set openunison.dns_suffix kargo.tremolo.dev
```

Set the client_id

```
pulumi config set openunison.github.client_id
```

Set the client secret

```
pulumi config set openunison.github.client_secret 'XXXXXXXXXXXXXXXXXXXXXXXXXXX' --secret
```

set the list of allowed teams in the form `org/team` or `org/` for the entire GitHub org you created.

```
pulumi config set openunison.github.teams 'TremoloSecurity/'
```

# Inviting Friends

If you want to allow more users to access your cluster, add them to the team you created in your GitHub org.

# Using OpenUnison

See our manual - https://openunison.github.io/documentation/login-portal/
