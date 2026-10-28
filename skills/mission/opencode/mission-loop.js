import { readFile, writeFile, unlink } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
const skill = fileURLToPath(new URL("../SKILL.md", import.meta.url));
const afkSkill = path.join(path.dirname(skill), "AFK.md");
const helpFile = path.join(path.dirname(skill), "HELP.md");
const setupFile = path.join(path.dirname(skill), "SETUP.md");
const helpSessions = new Set();
const setupSessions = new Set();
const inFlight = new Set();
const unownedWarnings = new Set();
function loopConfig(raw, directory) {
  const data = raw.trim().startsWith("{")
    ? JSON.parse(raw)
    : Object.fromEntries(raw.split(/\r?\n/).filter(Boolean).map((line) => line.split(/[:=]\s*/, 2)));
  if (!data.ledger || typeof data.ledger !== "string") throw new Error(".loop needs ledger");
  return { ...data, ledger: path.resolve(directory, data.ledger), max_rounds: Number(data.max_rounds ?? 20) };
}
async function sameLoop(file, snapshot) {
  try { return await readFile(file, "utf8") === snapshot; }
  catch (error) { if (error.code === "ENOENT") return false; throw error; }
}
async function writeLoop(file, snapshot, loop) {
  if (!await sameLoop(file, snapshot)) return null;
  const updated = JSON.stringify(loop) + "\n";
  await writeFile(file, updated);
  return updated;
}
function executionModel(loop, messages) {
  if (loop.model?.providerID && loop.model?.modelID) {
    return { model: loop.model, ...(loop.variant ? { variant: loop.variant } : {}) };
  }
  const infos = messages.map((message) => message.info).filter(Boolean)
    .sort((a, b) => (b.time?.created ?? 0) - (a.time?.created ?? 0));
  const assistant = infos.find((message) => message.role === "assistant");
  if (!assistant?.providerID || !assistant?.modelID) throw new Error("Cannot resume mission without the initiating model; no default model was selected");
  const user = infos.find((message) => message.id === assistant.parentID);
  const variant = assistant.variant ?? user?.variant ?? user?.model?.variant;
  return { model: { providerID: assistant.providerID, modelID: assistant.modelID }, ...(variant ? { variant } : {}) };
}
function unticked(ledger) {
  return ledger.split(/\r?\n/).filter((line) => /^- \[ \]/.test(line) || /^- \[x\]/.test(line) && !/— evidence: .+ → .+/.test(line)).length;
}
function progress(ledger) { return ledger.split(/\r?\n/).filter((line) => /^- \[x\].*— evidence: .+ → .+/.test(line)).length; }
function stopReason(loop, ledger, count, previous, stalled) {
  if (!loop) return null;
  const blockers = ledger.split(/\r?\n/).filter((line) => line.startsWith("BLOCKED:"));
  const emptyBlockers = new Set(["", "none", "n/a", "na", "no", "not blocked", "no blockers"]);
  if (blockers.some((line) => !emptyBlockers.has(line.slice("BLOCKED:".length).trim().replace(/[.!]+$/, "").toLowerCase()))) return "blocked";
  const left = unticked(ledger);
  if (!left) return "done";
  if (count >= loop.max_rounds) return "round cap";
  if (previous === progress(ledger) && stalled >= 2) return "no progress";
  return null;
}
function notify(message) {
  spawn("terminal-notifier", ["-title", "Mission loop", "-message", message], { stdio: "ignore" }).on("error", () => {});
}
export const MissionLoopPlugin = async ({ client, directory }) => ({
  config: async (config) => {
    config.command ??= {};
    config.command.mission = { description: "Orchestrate a plan or objective; setup installs the runtime, help shows usage, --afk runs unattended",
      template: `Read ${skill} and follow it. Mission arguments: $ARGUMENTS`, agent: "mission" };
    const current = config.permission?.skill;
    config.permission ??= {};
    config.permission.skill = typeof current === "object" && current !== null
      ? { ...current, mission: "deny" } : { "*": current ?? "allow", mission: "deny" };
  },
  "command.execute.before": async (input, output) => {
    if (input.command !== "mission") return;
    const args = input.arguments.trim();
    if (args === "setup") {
      setupSessions.add(input.sessionID);
      output.parts = [{ type: "text", text: `Read ${setupFile} and follow it to set up the mission OpenCode runtime: agents, plugins, and a model profile from MODEL_DEFAULTS.md with the user's choices. This is setup only: do not create or modify ledgers, .loop, branches, worker assignments, or mission files, and do not resume an existing mission. Change only the files SETUP.md names, report what changed, and include the restart the user needs.` }];
    } else if (["help", "--help", "-h"].includes(args)) {
      helpSessions.add(input.sessionID);
      output.parts = [{ type: "text", text: `Read ${helpFile} and explain how to use mission. This is help only: do not create or modify ledgers, .loop, branches, worker assignments, or project files, and do not resume an existing mission. Return after showing help.` }];
    } else {
      helpSessions.delete(input.sessionID);
      setupSessions.delete(input.sessionID);
    }
  },
  event: async ({ event }) => {
    const id = event?.properties?.sessionID;
    if (event?.type !== "session.idle" || !id) return;
    if (helpSessions.delete(id) || setupSessions.delete(id)) return;
    const file = path.join(directory, ".loop");
    if (!existsSync(file) || inFlight.has(file)) return;
    inFlight.add(file);
    try {
      const session = await client.session.get({ path: { id } });
      if (session.error || session.data?.parentID) return;
      let snapshot = await readFile(file, "utf8");
      const loop = loopConfig(snapshot, directory);
      if (loop.session && loop.session !== id) return;
      let messages = null;
      if (!loop.session) {
        const response = await client.session.messages({ path: { id }, query: { limit: 20 } });
        if (response.error) throw response.error;
        messages = response.data ?? [];
        const latest = messages.map((message) => message.info).filter((message) => message?.role === "assistant")
          .sort((a, b) => (b.time?.created ?? 0) - (a.time?.created ?? 0))[0];
        if (latest?.agent !== "mission") {
          if (!unownedWarnings.has(id)) {
            unownedWarnings.add(id);
            await client.app.log({ body: { service: "mission-loop", level: "warn",
              message: `Unbound .loop left unchanged: session ${id} did not run the mission agent. Start /mission in its owning session.` } });
          }
          return;
        }
        unownedWarnings.delete(id);
      }
      const ledger = await readFile(loop.ledger, "utf8");
      const state = { rounds: loop.state?.rounds ?? 0, previous: loop.state?.previous ?? null, stalled: loop.state?.stalled ?? 0 };
      if (![state.rounds, state.stalled, loop.max_rounds].every((value) => Number.isSafeInteger(value) && value >= 0)
        || state.previous !== null && (!Number.isSafeInteger(state.previous) || state.previous < 0)) {
        throw new Error(".loop has invalid round or progress counters");
      }
      state.stalled = state.previous === progress(ledger) ? state.stalled + 1 : 0;
      const reason = stopReason(loop, ledger, state.rounds, state.previous, state.stalled);
      if (reason) {
        if (!await sameLoop(file, snapshot)) return;
        await unlink(file);
        notify(`mission ${reason}: ${loop.ledger}`);
        return;
      }
      if ((!loop.model?.providerID || !loop.model?.modelID) && messages === null) {
        const response = await client.session.messages({ path: { id }, query: { limit: 20 } });
        if (response.error) throw response.error;
        messages = response.data ?? [];
      }
      const selected = executionModel(loop, messages ?? []);
      if (!loop.session || !loop.model?.providerID || !loop.model?.modelID) {
        snapshot = await writeLoop(file, snapshot, { ...loop, session: id, agent: "mission", ...selected });
        if (snapshot === null) return;
      }
      if (!await sameLoop(file, snapshot)) return;
      const afk = loop.mode === "afk";
      const result = await client.session.promptAsync({ path: { id }, body: {
        agent: "mission", ...selected,
        parts: [{ type: "text", synthetic: true,
          text: afk
            ? `Continue /mission --afk using ${loop.ledger}. Follow ${afkSkill} § Round. Resume any claimed batch before dispatching new work. Complete one ready batch, await its workers, verify the results, and update the ledger before yielding. Keep AFK decisions provisional and use the configured judge; do not turn them into human approval.`
            : `Continue /mission using ${loop.ledger}. Follow ${skill} § Round. Resume any claimed batch before dispatching new work. Complete one ready batch, await its workers, verify the results, and update the ledger before yielding.` }],
      } });
      if (result.error) throw result.error;
      state.previous = progress(ledger);
      state.rounds++;
      await writeLoop(file, snapshot, { ...loop, session: id, agent: "mission", ...selected, state });
    } catch (error) {
      await client.app.log({ body: { service: "mission-loop", level: "error", message: String(error) } });
    } finally {
      inFlight.delete(file);
    }
  },
});
