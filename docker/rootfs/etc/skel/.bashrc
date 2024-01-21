# .bashrc
test -r "~/.dir_colors" && eval $(dircolors ~/.dir_colors)
# User specific environment and startup programs
# Source items only for interactive sessions (Fixes qemu+ssh header size error)
case $- in *i*)
  for i in $(ls ~/.bashrc.d/ 2>/dev/null); do
    source ~/.bashrc.d/$i
  done
  for i in $(ls ~/deploy/.profile.d/ 2>/dev/null); do
    source ~/deploy/profile.d/$i
  done
esac

# Git stage/commit/push function
# Example:
#  - cd ~/Git/projectName
#  - touch 1.txt
#  - gitup add text file
# Git stage/commit/push
gitup () {

  git pull
  git_commit_msg="$@"
  git_branch=$(git branch --show-current)
  git_remote=$(git remote get-url --push origin)
  git_remote_push="$(git remote get-url --push origin | awk -F'[@]' '{print $2}')"

  cat <<EOF

  Commiting to:
    - branch:    ${git_branch}
    - remote:    ${git_remote_push}
    - message:   ${git_commit_msg}

EOF

  git stage -A
  git commit -m "${git_commit_msg}" --signoff
  git push
}

eval "$(direnv hook bash)"
eval "$(starship init bash)"

# User Alias(s)
alias quit="tmux detach"
alias ll="ls -lah"
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias cloc="git count | xargs wc -l 2>/dev/null"
alias k="kubectl"