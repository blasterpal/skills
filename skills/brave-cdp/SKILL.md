---
name: brave-cdp
description: Connect browser automation to the user's running Brave through its CDP debugging port. Use for "Brave CDP", attaching to an existing Brave session, or browser tasks when the user's instructions prefer Brave. Checks readiness and includes a launcher for the user to run when unavailable.
---

# Brave CDP

"Brave CDP" means attach to the Brave the user runs with remote debugging enabled.
The default endpoint is `http://127.0.0.1:9222`. This is an existing interactive browser;
the phrase does not request a new headless browser or a fresh profile.

## Check before attaching

Run the bundled check using this skill's installed path:

```sh
python3 "<skill-dir>/scripts/check_cdp.py"
```

It checks `/json/version` with a short timeout and prints the current browser WebSocket URL.
A listening port or a running Brave process alone does not prove CDP is ready.
Brave can report `Chrome/...` in its CDP metadata. On macOS, confirm that the listener
belongs to Brave with `lsof -nP -iTCP:9222 -sTCP:LISTEN` and `ps -p <pid> -o comm=`.
If another browser owns the port, report that conflict and wait for the user to resolve it.

If the check fails, pause browser-dependent work and prompt the user:

> Brave CDP is unavailable at http://127.0.0.1:9222. Run `"<skill-dir>/scripts/brave-cdp" start` in your terminal, then tell me when it's ready.

Replace `<skill-dir>` with this skill's actual installed absolute path and quote it
so the user can paste the command. The launcher is bundled at
[scripts/brave-cdp](scripts/brave-cdp). Let the user start
Brave, choose a profile, and complete sign-in or MFA. Do not launch, kill, or restart the
browser, create a profile, or change its debugging configuration on their behalf.
After their reply, rerun the check before attaching. Continue independent work while waiting.

The bundled launcher runs on macOS with Brave installed at `/Applications/Brave Browser.app`.
`start` reuses an existing listener or opens Brave with the persistent profile at
`~/.brave-cdp-profile`, prompting before its first creation. `status` checks the port.
The optional `start --profile <name>` uses a real Brave profile; the user must fully
quit that Brave instance first. `kill` stops the listener and is for the user to run
explicitly. These launcher commands use port 9222; for an explicitly supplied custom
endpoint, ask the user to start that endpoint with their own command.

## Attach and verify

1. Discover the available browser tools and use their documented existing-browser/CDP
   connection option. Configure the HTTP endpoint above, or use the fresh
   `webSocketDebuggerUrl` from the check when a tool requires WebSocket transport.
   Use a different endpoint only when the user explicitly supplies it; the check accepts
   that endpoint as its optional argument.
2. If no available browser tool supports CDP attachment, use an installed automation
   library that does. For Playwright, use `chromium.connectOverCDP(endpoint)` in
   JavaScript or `chromium.connect_over_cdp(endpoint)` in Python. Reuse an existing
   browser context and inspect its pages before selecting the relevant tab.
3. Confirm attachment by listing tabs or reading a page URL/title through the attached
   tool. Passing the readiness check alone does not prove the tool connected to Brave.
   If attachment fails, report the tool error and resolve that connection; keep the
   existing Brave session as the target.

Use attach operations, never `launch`, `launchPersistentContext`, or a tool's default
fresh browser. A tool limited to its own browser or native UI is not a CDP attachment;
if no attachment capability is available, explain the limitation rather than silently
switching browsers. Use installed dependencies first and ask before changing persistent
tool configuration or installing a browser automation dependency.

## Keep the session consistent

Reuse the attached context so the user's cookies and logins persist. Preserve unrelated
tabs and leave Brave running when finished; disconnect the client without issuing a
browser shutdown command. After a lost connection, rerun the check and obtain a fresh
WebSocket URL instead of launching a replacement browser.

When delegating browser work, give every worker this skill's path, the same endpoint,
and the selected tab ID/URL. Assign separate tabs for independent tasks and coordinate
any shared-tab mutations. Each worker must attach to the same running Brave.
This instruction does not itself authorize delegation.

Apply the user's existing authorization rules to actions performed in the browser.
