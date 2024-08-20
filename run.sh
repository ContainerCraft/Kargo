#!/bin/bash -x
pwd
printenv
whoami
source ~/.bashrc
eval "$(direnv hook bash)"
direnv allow
pulumi login
pwd
printenv
whoami
exec "@"
