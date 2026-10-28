#!/usr/bin/env bash
# Releases and publishes the configurator's print files, from a clean checkout on the host:
#   ./release-configurator.sh        merge the open release pull request (when there is one), then publish for the latest release
#   ./release-configurator.sh v1.2.3 publish for that release only
# Publishing builds the print files from the release tag, attaches configurator-<tag>.tar.gz to the release and
# redeploys the site. The merge waits for the required checks of the release pull request.
set -euo pipefail
[[ -z "$(git status --porcelain)" ]] || { echo "working tree is not clean" >&2; exit 1; }
tag=${1:-}
if [[ -z "$tag" ]]; then
  before=$(gh release view --json tagName --jq .tagName)
  # a pull request with the label hold is left alone by the workflow
  if [[ -n "$(gh pr list --label 'autorelease: pending' --json number,labels --jq '[.[] | select(all(.labels[]; .name != "hold"))][0].number // empty')" ]]; then
    run_id() { gh run list --workflow "$1" --limit 1 --json databaseId --jq '.[0].databaseId // 0'; }
    last=$(run_id release-weekly.yml)
    lastrel=$(run_id release.yml)
    gh workflow run release-weekly.yml
    until run=$(run_id release-weekly.yml); [[ "$run" != "$last" ]]; do sleep 5; done
    gh run watch "$run" --exit-status
    # the release workflow creates the release after the merge; wait up to 30 min
    for _ in $(seq 90); do
      if [[ "$(gh release view --json tagName --jq .tagName)" != "$before" ]]; then break; fi
      if [[ -n "$(gh run list --workflow release.yml --limit 1 --json databaseId,conclusion --jq ".[0] | select(.databaseId > $lastrel and .conclusion == \"failure\") | .databaseId")" ]]; then
        echo "release workflow failed" >&2; exit 1
      fi
      sleep 20
    done
  else
    echo "no release pull request to merge (none open, or held), publishing for $before"
  fi
  tag=$(gh release view --json tagName --jq .tagName)
  if [[ "$tag" = "${before:-}" ]] && [[ -n "${run:-}" ]]; then echo "no new release after 30 min" >&2; exit 1; fi
fi
git fetch --tags --quiet
back=$(git symbolic-ref --short -q HEAD || git rev-parse HEAD)
trap 'git switch --quiet "$back" 2>/dev/null || git switch --quiet --detach "$back"' EXIT
git switch --quiet --detach "$tag"
rm -rf build/configurator
# the container's .venv was installed from the lock it was created with, not necessarily the tag's
devcontainer exec --docker-path podman --workspace-folder . .venv/bin/pip install --quiet -r pylock.toml
devcontainer exec --docker-path podman --workspace-folder . .venv/bin/python build.py --no-test --configurator
archive=$(mktemp -d)/configurator-$tag.tar.gz
tar -czf "$archive" -C build/configurator .
gh release upload "$tag" "$archive" --clobber
gh workflow run pages.yml
