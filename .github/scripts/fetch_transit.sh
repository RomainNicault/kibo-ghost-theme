#!/usr/bin/env bash
# Fetches the transit refs read by promote_candidate.py into refs/transit/, with
# the read-only deploy key in TRANSIT_KEY; the key file is removed on exit.
# Prints nothing on success; one fixed error line otherwise.
set +x
set -uo pipefail
key="$RUNNER_TEMP/transit_key"; hosts="$RUNNER_TEMP/known_hosts"
trap 'rm -f "$key"' EXIT
install -m 600 /dev/null "$key"
printf '%s\n' "$TRANSIT_KEY" > "$key"
echo "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl" > "$hosts"
export GIT_SSH_COMMAND="ssh -i $key -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$hosts -o User=git"
url=ssh://github.com/RomainNicault/kibo-ghost-theme-transit.git
refs=("+refs/heads/main:refs/transit/main" "+refs/tags/deployed/*:refs/transit/deployed/*")
if git ls-remote --exit-code "$url" refs/heads/publication >/dev/null 2>&1; then
  refs+=("+refs/heads/publication:refs/transit/publication")
fi
git fetch -q --no-tags "$url" "${refs[@]}" >/dev/null 2>&1 || { echo "::error::transit fetch failed"; exit 1; }
