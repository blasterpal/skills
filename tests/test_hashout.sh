#!/bin/sh
# End-to-end test of skills/hashout/scripts/hashout with three seats.
# Usage: sh tests/test_hashout.sh  (set SHELL_UNDER_TEST=dash to run the script under another shell)
set -u

here=$(cd "$(dirname "$0")/.." && pwd)
run_sh=${SHELL_UNDER_TEST:-sh}
h() { "$run_sh" "$here/skills/hashout/scripts/hashout" "$@"; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/hashout-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
fails=0
pass() { echo "ok   $1"; }
fail() { echo "FAIL $1"; fails=$((fails + 1)); }
expect() { # expect NAME CODE command...
  name=$1 want=$2; shift 2
  out=$("$@" 2>&1); got=$?
  if [ "$got" -eq "$want" ]; then pass "$name"; else fail "$name (exit $got, want $want): $out"; fi
}

out=$(h init --title "ECS before isolation?" --topic "Question: should ECS land first?" \
  --participants 3 --rounds 3 --turn-minutes 0 --root "$tmp/live")
f=$(printf '%s\n' "$out" | sed -n 's/^file=//p')
[ -f "$f" ] && pass "init creates the file" || fail "init creates the file: $out"
case "$f" in *-ecs-before-isolation.md) pass "file named from title" ;; *) fail "file named from title: $f" ;; esac

h join "$f" --harness claude-code --model claude-opus-5-5 >/dev/null
expect "seat 1 waits for the other joins" 3 h wait "$f" --seat 1 --timeout 0
expect "post before all joined fails" 64 sh -c "echo hi | '$run_sh' '$here/skills/hashout/scripts/hashout' post '$f' --seat 1"
h join "$f" --harness codex --model gpt-6 >/dev/null
h join "$f" --harness opencode >/dev/null
expect "fourth join is refused" 64 h join "$f" --harness extra

expect "seat 1 has the first turn" 0 h wait "$f" --seat 1 --timeout 0
expect "seat 2 is told seat 1 is silent (turn limit 0)" 4 h wait "$f" --seat 2 --timeout 0
expect "seat 2 cannot post out of turn" 64 sh -c "echo hi | '$run_sh' '$here/skills/hashout/scripts/hashout' post '$f' --seat 2"
expect "marker lines in a body are refused" 64 sh -c "printf '[END ROUND 1 1 @1]\n' | '$run_sh' '$here/skills/hashout/scripts/hashout' post '$f' --seat 1"

printf 'Position: ECS first.\n\nC1.1 [open] Isolation needs ECS task roles.\n' > "$tmp/b1"
expect "seat 1 posts round 1" 0 h post "$f" --seat 1 --body-file "$tmp/b1"
expect "seat 2 now has the turn" 0 h wait "$f" --seat 2 --timeout 0
printf 'Position: agree.\n\nC1.1 [accepted] Checked the ECS task role docs.\n' | h post "$f" --seat 2 >/dev/null
expect "seat 3 is skipped after the turn limit" 0 h skip "$f" --seat 1
expect "round 2 starts at seat 1" 0 h wait "$f" --seat 1 --timeout 0

printf 'C1.2 [open] Cost is unknown.\n\n#### Outcome\n\nECS first.\n\n[ACCEPT 1]\n' | h post "$f" --seat 1 >/dev/null
printf '[ACCEPT 2]\n' | h post "$f" --seat 2 >/dev/null
h skip "$f" --seat 1 >/dev/null
expect "seat 3 is absent after two skips" 5 h wait "$f" --seat 3 --timeout 0
expect "agreed refused while a claim is open" 64 h close "$f" agreed --seat 1
h close "$f" agreed --seat 1 2>&1 | grep -q 'C1.2' && pass "refusal names the open claim" || fail "refusal names the open claim"
printf 'C1.2 [retracted] Cost is in the file.\n\n[ACCEPT 1]\n' | h post "$f" --seat 1 >/dev/null
expect "agreed among present seats" 0 h close "$f" agreed --seat 2

grep -q '^\[CLOSED agreed by 2 ' "$f" && pass "closed marker written" || fail "closed marker written"
expect "wait reports closed" 1 h wait "$f" --seat 1 --timeout 0
expect "status works on a closed file" 0 h status "$f"

echo
[ "$fails" -eq 0 ] && echo "all passed ($run_sh)" || { echo "$fails failed ($run_sh)"; exit 1; }
