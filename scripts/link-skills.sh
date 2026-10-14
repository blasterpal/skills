#!/usr/bin/env bash
# Link this checkout into the global skill directories for development.
set -euo pipefail

case "${1:-}" in
  "") dry_run=0 ;;
  --dry-run) dry_run=1 ;;
  --help|-h) echo "usage: scripts/link-skills.sh [--dry-run]"; exit 0 ;;
  *) echo "usage: scripts/link-skills.sh [--dry-run]" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "usage: scripts/link-skills.sh [--dry-run]" >&2; exit 2; }

repo="$(cd "$(dirname "$0")/.." && pwd)"
dests=("$HOME/.claude/skills" "$HOME/.agents/skills" "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills")
status=0
for skill_dir in "$repo"/skills/*/; do
  [[ -f "$skill_dir/SKILL.md" ]] || continue
  skill="$(basename "$skill_dir")"
  src="${skill_dir%/}"
  for dest in "${dests[@]}"; do
    target="$dest/$skill"
    if [[ -e "$target" && ! -L "$target" ]]; then
      echo "skip   $target exists and is not a symlink; move it yourself to use this checkout" >&2
      status=1
      continue
    fi
    if [[ -L "$target" && "$(readlink "$target")" == "$src" ]]; then
      echo "ok     $target"
      continue
    fi
    if [[ -L "$target" ]]; then
      echo "relink $target (was $(readlink "$target"))"
    else
      echo "link   $target"
    fi
    if (( ! dry_run )); then
      mkdir -p "$dest"
      ln -sfn "$src" "$target"
    fi
  done
done
(( dry_run )) && echo "dry run; nothing changed"
exit "$status"
