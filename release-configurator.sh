#!/usr/bin/env bash
# Releases and publishes the configurator's print files, from a clean checkout on the host:
#   ./release-configurator.sh        merge the open release pull request (when there is one), then publish for the latest release
#   ./release-configurator.sh v1.2.3 publish for that release only
# Publishing builds the print files from the release tag, attaches configurator-<tag>.tar.gz to the release and
# redeploys the site. The merge waits for the required checks of the release pull request.
set -euo pipefail
test -z "$(git status --porcelain)" || { echo "working tree is not clean" >&2; exit 1; }
tag=${1:-}
if [ -z "$tag" ]; then
  before=$(gh release view --json tagName --jq .tagName)
  if [ -n "$(gh pr list --label 'autorelease: pending' --json number --jq '.[0].number // empty')" ]; then
    last=$(gh run list --workflow release-weekly.yml --limit 1 --json databaseId --jq '.[0].databaseId // 0')
    gh workflow run release-weekly.yml
    until [ "$(gh run list --workflow release-weekly.yml --limit 1 --json databaseId --jq '.[0].databaseId')" != "$last" ]; do sleep 5; done
    gh run watch "$(gh run list --workflow release-weekly.yml --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
    # the release workflow creates the release after the merge
    until [ "$(gh release view --json tagName --jq .tagName)" != "$before" ]; do sleep 20; done
  else
    echo "no release pull request open, publishing for $before"
  fi
  tag=$(gh release view --json tagName --jq .tagName)
fi
git fetch --tags --quiet
back=$(git symbolic-ref --short -q HEAD || git rev-parse HEAD)
trap 'git switch --quiet "$back" 2>/dev/null || git switch --quiet --detach "$back"' EXIT
git switch --quiet --detach "$tag"
rm -rf build/configurator
devcontainer exec --docker-path podman --workspace-folder . .venv/bin/python build.py --no-test --configurator
archive=$(mktemp -d)/configurator-$tag.tar.gz
tar -czf "$archive" -C build/configurator .
gh release upload "$tag" "$archive" --clobber
gh workflow run pages.yml
