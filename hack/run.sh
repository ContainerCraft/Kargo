#!/bin/bash
#docker kill konductor

docker run -it --rm --pull=always --name konductor --hostname konductor \
          --user vscode \
          --publish 2222:2222 \
          --publish 7681:7681 \
          --publish 8088:8080 \
          --publish 32767:32767 \
          --cap-add=CAP_AUDIT_WRITE \
          --volume $PWD:/home/vscode/konductor:z \
          --entrypoint fish --workdir /home/vscode \
          --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
        ghcr.io/containercraft/konductor:latest

#         --user $(id -u):$(id -g) \
#         --volume="/etc/group:/etc/group:ro" \
#         --volume="/etc/passwd:/etc/passwd:ro" \
#         --volume="/etc/shadow:/etc/shadow:ro" \
#         --volume $PWD:/home/vscode/konductor:z \

#docker run -d --rm --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock --cap-add=CAP_AUDIT_WRITE --publish 2222:2222 --publish 7681:7681 --publish 8088:8080 --name konductor --hostname konductor --security-opt label=disable --pull=always ghcr.io/containercraft/konductor
#podman run -d --rm --cap-add=CAP_AUDIT_WRITE --publish 2222:2222 --publish 7681:7681 --publish 8088:8080 --name konductor --hostname konductor --security-opt label=disable --pull=always ghcr.io/containercraft/konductor