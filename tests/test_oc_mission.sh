#!/bin/sh
# Tests for the mission profile launcher (skills/mission/opencode/oc-mission).
# Usage: sh tests/test_oc_mission.sh  (set SHELL_UNDER_TEST=dash to run under another shell)
set -u

here=$(cd "$(dirname "$0")/.." && pwd)
run_sh=${SHELL_UNDER_TEST:-sh}
launcher="$here/skills/mission/opencode/oc-mission"
tmp=$(mktemp -d "${TMPDIR:-/tmp}/oc-mission-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
fails=0
pass() { echo "ok   $1"; }
fail() { echo "FAIL $1"; fails=$((fails + 1)); }
expect() { # expect NAME CODE command...
  name=$1 want=$2; shift 2
  out=$("$@" 2>&1); got=$?
  if [ "$got" -eq "$want" ]; then pass "$name"; else fail "$name (exit $got, want $want): $out"; fi
}

# Stub opencode reports the config it received plus the arguments it was passed.
mkdir -p "$tmp/bin"
cat > "$tmp/bin/opencode" <<'STUB'
#!/bin/sh
printf 'opencode config=%s args=%s\n' "${OPENCODE_CONFIG-}" "$*"
STUB
chmod +x "$tmp/bin/opencode"
profiles="$tmp/.config/opencode/profiles"
mkdir -p "$profiles"
printf '{}\n' > "$profiles/mission-default.json"
printf '{}\n' > "$profiles/mission-team.json"

run() { # run [launcher args...] inside the stub environment
  HOME="$tmp" XDG_CONFIG_HOME= PATH="$tmp/bin:$PATH" "$run_sh" "$launcher" "$@"
}

out=$(run --help)
case "$out" in *Usage:*) pass "--help prints usage" ;; *) fail "--help prints usage: $out" ;; esac
expect "--profile without a value is refused" 2 run --profile
expect "profile name with a slash is refused" 2 run --profile ../evil
expect "profile name with a space is refused" 2 run --profile "a b"
expect "empty profile name is refused" 2 run --profile=
expect "missing profile is an error" 1 run --profile nosuch

out=$(run)
case "$out" in "opencode config=$profiles/mission-default.json args=") pass "default profile selected" ;; *) fail "default profile selected: $out" ;; esac
out=$(run --profile team)
case "$out" in "opencode config=$profiles/mission-team.json args=") pass "--profile name selects the profile" ;; *) fail "--profile name selects the profile: $out" ;; esac
out=$(run --profile=team)
case "$out" in "opencode config=$profiles/mission-team.json args=") pass "--profile=name selects the profile" ;; *) fail "--profile=name selects the profile: $out" ;; esac
out=$(run --profile team run --afk goal)
case "$out" in "opencode config=$profiles/mission-team.json args=run --afk goal") pass "extra arguments pass through" ;; *) fail "extra arguments pass through: $out" ;; esac

# An executable ~/.local/bin/oc wrapper takes precedence over opencode on PATH.
mkdir -p "$tmp/.local/bin"
cat > "$tmp/.local/bin/oc" <<'STUB'
#!/bin/sh
printf 'oc-wrapper config=%s args=%s\n' "${OPENCODE_CONFIG-}" "$*"
STUB
chmod +x "$tmp/.local/bin/oc"
out=$(run)
case "$out" in "oc-wrapper config=$profiles/mission-default.json args=") pass "oc wrapper preferred over opencode" ;; *) fail "oc wrapper preferred over opencode: $out" ;; esac

# XDG_CONFIG_HOME moves the profile directory.
mkdir -p "$tmp/xdg/opencode/profiles"
printf '{}\n' > "$tmp/xdg/opencode/profiles/mission-xdg.json"
out=$(HOME="$tmp" XDG_CONFIG_HOME="$tmp/xdg" PATH="$tmp/bin:$PATH" "$run_sh" "$launcher" --profile xdg)
case "$out" in *"config=$tmp/xdg/opencode/profiles/mission-xdg.json"*) pass "XDG_CONFIG_HOME respected" ;; *) fail "XDG_CONFIG_HOME respected: $out" ;; esac

echo
[ "$fails" -eq 0 ] && echo "all passed ($run_sh)" || { echo "$fails failed ($run_sh)"; exit 1; }
