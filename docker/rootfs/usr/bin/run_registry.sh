#!/bin/bash
start () {
  unset REGISTRY_AUTH_FILE
  registry serve /etc/docker/registry/config.yml 2>&1 1>/dev/stderr &
}
start
