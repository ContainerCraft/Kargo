# This is the Konductor Dockerfile
# FROM the Microsoft Ubuntu 22.04 LTS Devcontainer Base Image
#
# The Konductor Container provides a Devcontainer developer userspace
# for use with VSCode, Github Codespaces, and Github Action Runners.
#
# The Konductor Container Image is a container image purpose built to provide
# a consistent and reliable development environment for DevOps tasks.
#
# The Konductor Container Image is not intended as an application container image
# and does not adhere to the principle of one service per container but rather
# is designed for one purpose per container.
#
###############################################################################
# Use:
# - docker build --tag ghcr.io/containercraft/konductor:latest .
# - docker run --rm --publish 2222:2222 --publish 7681:7681 --publish 8088:8080 -d --name konductor --hostname konductor ghcr.io/containercraft/konductor:latest
# - docker run -d --rm --cap-add=CAP_AUDIT_WRITE --publish 2222:2222 --publish 7681:7681 --publish 8088:8080 --name konductor --hostname konductor --security-opt label=disable --pull=always ghcr.io/containercraft/konductor
# - docker run -it --rm --entrypoint fish --mount type=bind,source=/run/docker.sock,target=/run/docker.sock --privileged --user vscode ghcr.io/containercraft/konductor:latest
###############################################################################
# Base VSCode Image
FROM mcr.microsoft.com/devcontainers/base:ubuntu
SHELL ["/bin/bash", "-c", "-e"]

# Github Token is used for github api calls to get latest releases
# This is optional but helps during development due to rate limiting)
# Note that this is a docker argument and not an environment variable (ARG vs ENV)
# so it is not persisted in the image layers and is not available
# at runtime (only build time)
ARG GITHUB_TOKEN=${GITHUB_TOKEN}

# Append rootfs directory tree into container to copy
# additional files into the container's directory tree
ADD rootfs /
ADD rootfs/etc/skel/ /root/
ADD rootfs/etc/skel/ /home/runner/
ADD rootfs/etc/skel/ /home/vscode/
RUN cat /etc/skel/.bashrc > /root/.bashrc && rm /root/.vimrc

#################################################################################
# Environment Variables

# Disable timezone prompts
ENV TZ=UTC
# Disable package manager prompts
ENV DEBIAN_FRONTEND=noninteractive
# Add go and nix to path
ENV PATH="/home/vscode/.krew/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/go/bin:/nix/var/nix/profiles/default/bin"
# Set necessary nix environment variable
ENV NIX_INSTALLER_EXTRA_CONF='filter-syscalls = false'
# Set default bin directory for new packages
ARG BIN="/usr/local/bin"
# Set default binary install command
ARG INSTALL="install -m 755 -o root -g root"
# Set additional environment variables
ENV SHELL=/usr/bin/fish
ENV REGISTRY_AUTH_FILE='/home/vscode/.docker/config.json'
ENV XDG_CONFIG_HOME=/home/vscode/.config

# Common Dockerfile Container Build Functions
ARG apt_update="sudo apt-get update"
ARG apt_install="TERM=linux DEBIAN_FRONTEND=noninteractive sudo apt-get install -q --yes --purge --assume-yes --auto-remove --allow-downgrades -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'"
ARG apt_clean="sudo apt-get clean && sudo apt-get autoremove -y && sudo apt-get purge -y --auto-remove"
ARG curl="/usr/bin/curl --silent --show-error --tlsv1.2 --location"
ARG curl_github="/usr/bin/curl --silent --show-error --tlsv1.2 --request GET --header "Authorization: Bearer $GITHUB_TOKEN" --header "X-GitHub-Api-Version: 2022-11-28" --url --location"
ARG dir_clean="\
sudo rm -rf \
/var/lib/{apt,cache,log} \
/usr/share/{doc,man,locale} \
/var/cache/apt \
/home/*/.cache \
/root/.cache \
/var/tmp/* \
/tmp/* \
"

#################################################################################
# Base package and user configuration
#################################################################################

# Apt Packages
ARG APT_PKGS="\
gh \
bc \
mc \
vim \
git \
tar \
mosh \
file \
wget \
tree \
pigz \
fish \
curl \
tmux \
tmate \
socat \
gnupg \
pipenv \
netcat \
psmisc \
procps \
passwd \
ripgrep \
tcpdump \
python3 \
pciutils \
libwrap0 \
xz-utils \
fontconfig \
glibc-tools \
python3-pip \
ca-certificates \
build-essential \
libarchive-tools \
neofetch \
"

# Apt Packages
RUN echo \
&& export TEST="neofetch" \
&& ${apt_update} \
&& bash -c "${apt_install} --no-install-recommends -o Dpkg::Options::='--force-confold' ${APT_PKGS}" \
&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends -o Dpkg::Options::='--force-confold' openssh-server \
&& mkdir /var/run/sshd \
&& bash -c "${apt_clean}" \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# devcontainer docker-in-docker dependencies
ARG APT_PKGS="\
docker-buildx-plugin \
docker-ce-cli \
libffi-dev \
iptables \
"
RUN echo \
&& ${curl} https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list \
&& ${apt_update} \
&& bash -c "${apt_install} ${APT_PKGS}" \
&& bash -c "${apt_clean}" \
&& ${dir_clean} \
&& sudo update-alternatives --set iptables /usr/sbin/iptables-legacy \
&& sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy \
&& echo

# jq
RUN echo \
&& export NAME="jq" \
&& export TEST="${NAME} --version" \
&& export REPOSITORY="jqlang/jq" \
&& export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | awk -F '[\"v\",-]' '/tag_name/{print $5}')" \
&& export PKG="${NAME}-linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${NAME}-${VERSION}/${NAME}-linux-${ARCH}" \
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& ${curl} ${URL} --output /tmp/${NAME} \
&& file /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# Nix
RUN echo \
&& export NAME=nix-installer \
&& export TEST="${NAME} --version" \
&& export REPOSITORY="DeterminateSystems/nix-installer" \
&& export VERSION="$(${curl_github} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "x86_64"; else if ($1 == "aarch64" || $1 == "arm64") print "aarch64"; else print "unknown" }') \
&& export PKG="${NAME}-${ARCH}-linux" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& sudo ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${NAME} install linux --init none --no-confirm --extra-conf "filter-syscalls = false" \
&& bash -c "${TEST}" \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# direnv
RUN echo \
&& export NAME="direnv"\
&& export PKG="install.sh"\
&& export URL="https://direnv.net/${PKG}"\
&& export TEST="${NAME} --version"\
&& echo "INFO[${NAME}] Install Package:"\
&& echo "INFO[${NAME}]  Command: ${NAME}"\
&& echo "INFO[${NAME}]  Package: ${PKG}"\
&& echo "INFO[${NAME}]  Source:  ${URL}"\
&& ${curl} ${URL} --output /tmp/${PKG} \
&& chmod +x /tmp/${PKG} \
&& sudo bash -c "/tmp/${PKG}" \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# Starship
RUN echo \
&& export NAME=starship \
&& export TEST="${NAME} --version" \
&& export URL="https://starship.rs/install.sh" \
&& ${curl} ${URL} --output /tmp/${NAME} \
&& chmod +x /tmp/${NAME} \
&& bash -c "/tmp/${NAME} --verbose --yes" \
&& ${dir_clean} \
&& ${TEST} \
&& echo

#################################################################################
# Create Users and Groups
# Create User: runner (for github actions runner support)

RUN echo \
&& sudo mkdir -p /etc/sudoers.d || true \
&& sudo groupadd --force --system sudo || true \
&& sudo groupadd --force --gid 127 --system docker \
&& sudo echo "%sudo ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/sudo \
&& sudo echo "%runner ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/sudo \
&& sudo echo "%vscode ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/sudo \
&& echo

# Set User & Workdir default to $HOME
USER vscode
WORKDIR /home/vscode

# Adduser:
# - user:   vscode
# - group:  vscode
# - uid:    1000
# - gid:    1000
RUN echo \
&& export USER_ID="1000" \
&& export USER_NAME="vscode" \
&& export USER_SHELL="fish" \
&& export USER_GROUPS="${USER_NAME},sudo,docker,vscode" \
&& export USER_GROUP_NAME="${USER_NAME}" \
&& export USER_GROUP_ID="${USER_ID}" \
&& echo "INFO[${USER_NAME}]  User:" \
&& echo "INFO[${USER_NAME}]    User Name:   ${USER_NAME}" \
&& echo "INFO[${USER_NAME}]    User Group:  ${USER_GROUP_NAME}" \
&& echo "INFO[${USER_NAME}]    Aux Groups:  ${USER_GROUPS}" \
&& echo "INFO[${USER_NAME}]    Group ID:    ${USER_GROUP_ID}" \
&& echo "INFO[${USER_NAME}]    User ID:     ${USER_ID}" \
&& echo "INFO[${USER_NAME}]    SHELL:       $(which ${USER_SHELL})" \
&& echo "${USER_NAME} ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers \
&& sudo groupadd --force --gid ${USER_ID} ${USER_NAME} \
&& sudo useradd --create-home --uid ${USER_ID} --gid ${USER_GROUP_ID} --shell $(which ${USER_SHELL}) --groups ${USER_GROUPS} ${USER_NAME} || true \
&& sudo usermod --append --groups ${USER_GROUPS} ${USER_NAME} \
&& sudo chsh --shell $(which ${USER_SHELL}) ${USER_NAME} \
&& sudo mkdir -p /home/vscode/.krew/bin \
&& sudo chmod 0755 -R /home/vscode/.krew/bin \
&& sudo chown ${USER_NAME}:${USER_NAME} -R /home/vscode/.krew/bin \
&& sudo su --preserve-environment --shell $(which ${USER_SHELL}) -c groups ${USER_NAME} 2>/dev/null \
&& sudo chmod 0775 /usr/local/lib \
&& sudo rm -rf /usr/local/lib/node_modules \
&& sudo mkdir -p /usr/local/lib/node_modules \
&& echo

RUN sudo chown vscode:vscode -R /home/vscode

# Adduser:
# - user:   runner
# - group:  runner
# - uid:    1001
# - gid:    1001
RUN echo \
&& export USER_ID="1001" \
&& export USER_NAME="runner" \
&& export USER_SHELL="bash" \
&& export USER_GROUPS="sudo,docker,vscode,runner" \
&& export USER_GROUP_ID="${USER_ID}" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}] User:" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}]   UID:         ${USER_ID}" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}]   NAME:        ${USER_NAME}" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}]   SHELL:       $(which ${USER_SHELL})" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}]   USER GROUP:  ${USER_GROUP_ID}" \
&& echo "INFO[${USER_NAME}:${USER_ID}:${USER_GROUPS}]   AUX GROUPS:  ${USER_GROUPS}" \
&& sudo groupadd --force --gid ${USER_ID} ${USER_NAME} \
&& sudo echo "${USER_NAME} ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers \
&& sudo useradd --create-home --uid ${USER_ID} --gid ${USER_GROUP_ID} --shell $(which ${USER_SHELL}) --groups ${USER_GROUPS} ${USER_NAME} \
&& sudo chsh --shell $(which ${USER_SHELL}) ${USER_NAME} \
&& sudo usermod --append --groups ${USER_GROUPS} ${USER_NAME} \
&& sudo usermod --append --groups ${USER_GROUPS} vscode \
&& sudo su --preserve-environment --shell $(which ${USER_SHELL}) -c groups ${USER_NAME} \
&& sudo chown runner:runner -R /home/runner \
&& sudo chmod 755 /home/vscode/.* \
&& echo

RUN sudo chown runner:runner -R /home/runner

##################################################################################
# Install Creature Comforts

# Oh My Fish (OMF)
RUN echo \
&& export URL="https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install" \
&& ${curl} ${URL} --output /tmp/install \
&& fish -c '. /tmp/install --noninteractive' \
&& ${dir_clean} \
&& echo

# Vim Plugins
RUN echo \
&& /bin/bash -c "vim -T dumb -n -i NONE -es -S <(echo -e 'silent! PluginInstall')" \
&& git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim \
&& vim -E -u NONE -S ~/.vimrc +PluginInstall +qall \
&& echo

# TMUX Plugins
RUN echo \
&& ~/.tmux/plugins/tpm/bin/install_plugins || true \
&& echo

# NerdFonts: FiraCode Nerd Font Mono
RUN echo \
&& export NAME=FiraMonoNerdFont \
&& export TEST="fc-list --quiet ${NAME}" \
&& export REPOSITORY="ryanoasis/nerd-fonts" \
&& export VERSION="$(${curl_github} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \
&& export PKG="FiraMono.zip" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& export DIR="/usr/share/fonts/truetype/firacode" \
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& ${curl} ${URL} --output /tmp/fonts.zip \
&& sudo mkdir -p $DIR \
&& sudo rm -rf $DIR/* \
&& sudo unzip /tmp/fonts.zip -d /usr/share/fonts/truetype/firacode \
&& sudo fc-cache -f -v \
&& fc-list : family | sort | uniq \
&& ${dir_clean} \
&& ${TEST} \
&& echo

#################################################################################
# Install Programming Language Tooling
# - golang
# - nodejs
# - python
# - dotnet
#################################################################################

# Install nodejs npm yarn
RUN echo \
&& export NODE_MAJOR=20 \
&& ${curl} https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
&& echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" \
    | sudo tee /etc/apt/sources.list.d/nodesource.list \
&& sudo apt-get update \
&& sudo apt-get install nodejs \
&& sudo apt-get clean \
&& sudo apt-get autoremove -y \
&& sudo apt-get purge -y --auto-remove \
&& ${dir_clean} \
&& node --version \
&& npm --version \
&& sudo npm install --global yarn \
&& yarn --version \
&& true

# Python
ARG APT_PKGS="\
python3 \
python3-pip \
python3-venv \
"
RUN echo \
&& bash -c "${apt_install} ${APT_PKGS}" \
&& bash -c "${apt_clean}" \
&& sudo update-alternatives --install \
    /usr/bin/python python \
    /usr/bin/python3 1 \
&& ${dir_clean} \
&& echo

# Python Pip Packages
ARG PIP_PKGS="\
setuptools \
"
RUN echo \
&& sudo python3 -m pip install ${PIP_PKGS} \
&& ${dir_clean} \
&& echo

# Dotnet
ARG APT_PKGS="\
dotnet-sdk-7.0 \
dotnet-runtime-7.0 \
"
RUN echo \
&& bash -c "${apt_install} ${APT_PKGS}" \
&& bash -c "${apt_clean}" \
&& ${dir_clean} \
&& echo

# Golang
RUN echo ;set -ex \
&& jq --version \
&& export NAME="go" \
&& export TEST="${NAME} version" \
&& export VERSION="$(${curl} "https://go.dev/dl/?mode=json" | jq --compact-output --raw-output .[1].version)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${VERSION}.linux-${ARCH}.tar.gz" \
&& export URL="https://go.dev/dl/${PKG}" \
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& ${curl} ${URL} | sudo tar -C /usr/local/ -xzvf - \
&& sudo chmod 755 /usr/local/go/bin/* \
&& ${TEST} \
&& echo

#################################################################################
# Image Metadata
LABEL name="Konductor"
LABEL io.k8s.display-name="Konductor"
LABEL maintainer="github.com/containercraft"
LABEL org.opencontainers.image.authors="github.com/containercraft"
LABEL io.openshift.tags="containercraft,konductor"
LABEL org.opencontainers.image.licenses="GPLv3"
LABEL distribution-scope="public"

##################################################################################
# Install k9s CLI
# - https://k9scli.io
# - https://github.com/derailed/k9s
RUN echo \
&& export NAME=k9s \
&& export TEST="${NAME} version" \
&& export REPOSITORY="derailed/k9s" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}_Linux_${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | sudo tar xzvf - --directory /tmp ${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

################################################################################
# Install Pulumi CLI, ESC, & CTL
# Install Pulumi CLI Utilities and Pulumi go deps
ARG GO_PKGS="\
golang.org/x/tools/gopls@latest \
github.com/josharian/impl@latest \
github.com/fatih/gomodifytags@latest \
github.com/cweill/gotests/gotests@latest \
github.com/go-delve/delve/cmd/dlv@latest \
honnef.co/go/tools/cmd/staticcheck@latest \
github.com/haya14busa/goplay/cmd/goplay@latest \
"
RUN echo \
&& export NAME=pulumi \
&& export TEST="pulumi version" \
&& export REPOSITORY="pulumi/pulumi" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "x64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-${VERSION}-linux-${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp \
&& sudo chmod 755 /tmp/pulumi/* \
&& sudo chown root:root /tmp/pulumi/* \
&& sudo mv /tmp/pulumi/* /usr/local/bin/ \
&& echo "+-------------------------------------------------------+"\
&& echo "|       Installing Basic Pulumi Golang Deps             |"\
&& echo "+-------------------------------------------------------+"\
&& for pkg in ${GO_PKGS}; do go install ${pkg}; echo "Installed: ${pkg}"; done \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# Install pulumi esc
RUN echo \
&& export NAME="esc" \
&& export TEST="esc version" \
&& export REPOSITORY="pulumi/esc" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "x64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-${VERSION}-linux-${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp \
&& sudo ${INSTALL} /tmp/${NAME}/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

# Install pulumictl
RUN echo \
&& export NAME="pulumictl" \
&& export TEST="${NAME} version" \
&& export REPOSITORY="pulumi/pulumictl" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-${VERSION}-linux-${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
#### Common Binary Install Arguments
##################################################################################

# Install yq
RUN echo \
&& export NAME="yq" \
&& export TEST="${NAME} --version" \
&& export REPOSITORY="mikefarah/yq" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}_linux_${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${NAME}_linux_${ARCH}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& sudo ${curl} ${URL} --output /tmp/yq \
&& sudo ${INSTALL} /tmp/yq ${BIN}/yq \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install Kubectl
# - https://kubernetes.io
# - github.com/kubernetes/kubernetes
RUN echo \
&& export NAME=kubectl \
&& export TEST="${NAME} version --client" \
&& export REPOSITORY="kubernetes/kubernetes" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}" \
&& export URL="https://storage.googleapis.com/kubernetes-release/release/${VERSION}/bin/linux/${ARCH}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& sudo ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/kubectl ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install ttyd
# - https://tsl0922.github.io/ttyd
# - https://github.com/tsl0922/ttyd
RUN echo \
&& export NAME=ttyd \
&& export TEST="${NAME} --version" \
&& export REPOSITORY="tsl0922/ttyd" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "x86_64"; else if ($1 == "aarch64" || $1 == "arm64") print "aarch64"; else print "unknown" }') \
&& export PKG="${NAME}.${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Insall Cilium CLI
# - https://cilium.io
# - https://github.com/cilium/cilium-cli
RUN echo \
&& export NAME=cilium \
&& export TEST="${NAME} version --client" \
&& export REPOSITORY="cilium/cilium-cli" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-linux-${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}"/${PKG} \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp ${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Insall istioctl
# - https://istio.io
# - https://github.com/istio/istio
# - https://github.com/istio/istio/releases/download/1.20.2/istio-1.20.2-linux-arm64.tar.gz
RUN echo \
&& export NAME=istioctl \
&& export TEST="${NAME} version --short 2>/dev/null" \
&& export REPOSITORY="istio/istio" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="istio-${VERSION}-linux-${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp istio-${VERSION}/bin/${NAME} \
&& sudo ${INSTALL} /tmp/istio-${VERSION}/bin/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Insall Github Actions Local Testing CLI
# - https://nektosact.com
# - https://github.com/nektos/gh-act
RUN echo \
&& export NAME=act \
&& export TEST="${NAME} --version" \
&& export REPOSITORY="nektos/gh-act" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Insall helm cli
# - https://helm.sh
# - https://github.com/helm/helm
RUN echo \
&& export NAME=helm \
&& export TEST="${NAME} version" \
&& export REPOSITORY="helm/helm" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-${VERSION}-linux-${ARCH}.tar.gz" \
&& export URL="https://get.helm.sh/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp linux-${ARCH}/${NAME} \
&& sudo ${INSTALL} /tmp/linux-${ARCH}/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install clusterctl
RUN echo \
&& export NAME=clusterctl \
&& export TEST="${NAME} version" \
&& export REPOSITORY="kubernetes-sigs/cluster-api" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export PKG="${NAME}-linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install talosctl
RUN echo \
&& export NAME=talosctl \
&& export TEST="${NAME} version --client" \
&& export REPOSITORY="siderolabs/talos" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \
&& export PKG="${NAME}-linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install virtctl
RUN echo \
&& export NAME=virtctl \
&& export TEST="${NAME} version --client" \
&& export REPOSITORY="kubevirt/kubevirt" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \
&& export PKG="${NAME}-${VERSION}-linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install Kind Kubernetes-in-Docker
RUN echo \
&& export NAME=kind \
&& export TEST="${NAME} version" \
&& export REPOSITORY="kubernetes-sigs/kind" \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \
&& export PKG="${NAME}-linux-${ARCH}" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command:        ${NAME}" \
&& echo "INFO[${NAME}]   Package:        ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release: ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
&& echo "INFO[${NAME}]   Source:         ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} --output /tmp/${NAME} \
&& sudo ${INSTALL} /tmp/${NAME} ${BIN}/${NAME} \
&& ${dir_clean} \
&& ${TEST} \
&& echo

##################################################################################
# Install Krew
ARG KREW_PKG="\
view-utilization \
view-secret \
view-cert \
rook-ceph \
open-svc \
whoami \
konfig \
ktop \
neat \
tail \
ctx \
ns \
"
RUN echo \
&& export NAME=krew \
&& export TEST="kubectl ${NAME} version" \
&& export REPOSITORY="kubernetes-sigs/${NAME}" \
&& export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
&& export VERSION="$(${curl} https://api.github.com/repos/${REPOSITORY}/releases/latest | jq --raw-output .tag_name)" \
&& export PKG="${NAME}-linux_${ARCH}.tar.gz" \
&& export URL="https://github.com/${REPOSITORY}/releases/download/${VERSION}/${PKG}" \
&& echo "---------------------------------------------------------"\
&& echo "INFO[${NAME}] Installed:" \
&& echo "INFO[${NAME}]   Command: (kubectl) ${NAME}" \
&& echo "INFO[${NAME}]   Package:           ${PKG}" \
&& echo "INFO[${NAME}]   Latest Release:    ${VERSION}" \
&& echo "INFO[${NAME}]   Architecture:      ${ARCH}" \
&& echo "INFO[${NAME}]   Source:            ${URL}" \
&& echo "---------------------------------------------------------"\
&& ${curl} ${URL} | tar xzvf - --directory /tmp ./${NAME}-linux_${ARCH} \
&& sudo ${INSTALL} /tmp/${NAME}-linux_${ARCH} ${BIN}/kubectl-${NAME} \
&& for pkg in ${CODE_PKGS}; do kubectl ${NAME} install ${pkg}; echo "Installed: ${pkg}"; done \
&& ${dir_clean} \
&& ${TEST} \
&& echo

#################################################################################
# Load startup artifacts
COPY ./bin/connect         /bin/
COPY ./bin/entrypoint      /bin/

#################################################################################
# Entrypoint & default command
ENTRYPOINT /bin/entrypoint
CMD ["/usr/bin/env", "connect"]

# Ports
# - mosh
EXPOSE 6000
# - TTYd
EXPOSE 7681
