import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdtemp, rm, access } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const sourcePath = new URL('./mission-loop.js', import.meta.url);
let sequence = 0;
const defaultMessages = [
  { info: { role: 'user', id: 'user-1', time: { created: 1 }, agent: 'mission', model: { providerID: 'profile-provider', modelID: 'selected-model', variant: 'high' } }, parts: [] },
  { info: { role: 'assistant', id: 'assistant-1', parentID: 'user-1', time: { created: 2 }, agent: 'mission', providerID: 'profile-provider', modelID: 'selected-model', variant: 'high' }, parts: [] },
];
async function fixture(t, { loop = {}, ledger = '- [ ] First batch\n', messages = defaultMessages, parentID, promptError, holdPrompt, holdMessages } = {}) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'mission-loop-test-'));
  const loopFile = path.join(directory, '.loop');
  const ledgerFile = path.join(directory, 'ledger.md');
  await writeFile(ledgerFile, ledger);
  await writeFile(loopFile, typeof loop === 'string' ? loop : JSON.stringify({ ledger: 'ledger.md', ...loop }));
  const key = `mission-plugin-test-${++sequence}`;
  globalThis[key] = [];
  let source = await readFile(sourcePath, 'utf8');
  source = source.replaceAll('import.meta.url', JSON.stringify(sourcePath.href));
  source = source.replace('import { spawn } from "node:child_process";', `const spawn = (...args) => { globalThis[${JSON.stringify(key)}].push(args); return { on() {} }; };`);
  let generation = 0;
  const loadPlugin = () => import(`data:text/javascript;base64,${Buffer.from(source + '\n//' + key + '-' + generation++).toString('base64')}`);
  let { MissionLoopPlugin } = await loadPlugin();
  const calls = { prompts: [], messages: 0, gets: [], logs: [], notifications: globalThis[key] };
  const client = {
    session: {
      get: async ({ path: params }) => { calls.gets.push(params); return { data: { id: params.id, parentID } }; },
      messages: async ({ path: params, query }) => { assert.equal(params.id, 'root'); assert.equal(query.limit, 20); calls.messages++; if (holdMessages) await holdMessages; return { data: messages }; },
      promptAsync: async (params) => { calls.prompts.push(params); if (holdPrompt) await holdPrompt; return promptError ? { error: promptError } : {}; },
    },
    app: { log: async (params) => { calls.logs.push(params.body); } },
  };
  let plugin = await MissionLoopPlugin({ client, directory });
  const restart = async () => {
    ({ MissionLoopPlugin } = await loadPlugin());
    plugin = await MissionLoopPlugin({ client, directory });
  };
  const emit = (sessionID = 'root', type = 'session.idle') => plugin.event({ event: { type, properties: { sessionID } } });
  const exists = async () => { try { await access(loopFile); return true; } catch { return false; } };
  t.after(async () => { delete globalThis[key]; await rm(directory, { recursive: true, force: true }); });
  return { plugin, calls, emit, restart, loopFile, ledgerFile, exists, directory };
}

test('mission command selects mission agent and retains skill permissions', async (t) => {
  const f = await fixture(t);
  const config = { permission: { skill: { '*': 'ask', research: 'allow' } } };
  await f.plugin.config(config);
  assert.equal(config.command.mission.agent, 'mission');
  assert.match(config.command.mission.template, /\$ARGUMENTS/);
  assert.deepEqual(config.permission.skill, { '*': 'ask', research: 'allow', mission: 'deny' });
});

test('first root idle binds session and preserves the actual model and variant', async (t) => {
  const f = await fixture(t, { loop: { mode: 'afk', max_rounds: 7 } });
  await f.emit();
  const binding = JSON.parse(await readFile(f.loopFile, 'utf8'));
  assert.equal(binding.session, 'root');
  assert.equal(binding.agent, 'mission');
  assert.equal(binding.ledger, f.ledgerFile);
  assert.equal(binding.mode, 'afk');
  assert.equal(binding.max_rounds, 7);
  assert.deepEqual(binding.model, { providerID: 'profile-provider', modelID: 'selected-model' });
  assert.equal(binding.variant, 'high');
  assert.equal(f.calls.prompts[0].body.agent, 'mission');
  assert.deepEqual(f.calls.prompts[0].body.model, binding.model);
  assert.equal(f.calls.prompts[0].body.variant, 'high');
  assert.match(f.calls.prompts[0].body.parts[0].text, /one ready batch/);
  assert.match(f.calls.prompts[0].body.parts[0].text, /configured judge/);
});

test('continuation uses persisted model even if message selection changes', async (t) => {
  const f = await fixture(t, { loop: { session: 'root', model: { providerID: 'chosen', modelID: 'economy' }, variant: 'balanced' } });
  await f.emit();
  assert.equal(f.calls.messages, 0);
  assert.deepEqual(f.calls.prompts[0].body.model, { providerID: 'chosen', modelID: 'economy' });
  assert.equal(f.calls.prompts[0].body.variant, 'balanced');
});

test('latest assistant model wins; parent user supplies absent assistant variant', async (t) => {
  const messages = [
    { info: { role: 'assistant', agent: 'mission', providerID: 'new', modelID: 'cheap', parentID: 'new-user', time: { created: 20 } } },
    { info: { role: 'assistant', providerID: 'old', modelID: 'expensive', time: { created: 2 } } },
    { info: { role: 'user', id: 'new-user', model: { variant: 'medium' }, time: { created: 19 } } },
  ];
  const f = await fixture(t, { messages });
  await f.emit();
  assert.deepEqual(f.calls.prompts[0].body.model, { providerID: 'new', modelID: 'cheap' });
  assert.equal(f.calls.prompts[0].body.variant, 'medium');
});

test('child session never binds, resumes, or removes the loop', async (t) => {
  const f = await fixture(t, { parentID: 'parent', ledger: '- [x] Done — evidence: check → pass\n' });
  const initial = await readFile(f.loopFile, 'utf8');
  await f.emit();
  assert.equal(await readFile(f.loopFile, 'utf8'), initial);
  assert.equal(f.calls.messages, 0);
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.notifications.length, 0);
});

test('bound loop ignores other root sessions and unrelated events', async (t) => {
  const f = await fixture(t, { loop: { session: 'owner' } });
  await f.emit();
  await f.emit('owner', 'message.updated');
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.messages, 0);
});

test('missing execution metadata leaves the loop without choosing a default', async (t) => {
  const f = await fixture(t, { messages: [{ info: { role: 'assistant', agent: 'mission', time: { created: 1 } } }] });
  await f.emit();
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(await f.exists(), true);
  assert.match(f.calls.logs[0].message, /without the initiating model/);
  assert.equal(JSON.parse(await readFile(f.loopFile, 'utf8')).session, undefined);
});

test('legacy ledger configuration still binds and resumes', async (t) => {
  const f = await fixture(t, { loop: 'ledger: ledger.md\nmax_rounds: 3\n' });
  await f.emit();
  const loop = JSON.parse(await readFile(f.loopFile, 'utf8'));
  assert.equal(loop.max_rounds, 3);
  assert.equal(loop.session, 'root');
  assert.equal(f.calls.prompts.length, 1);
});

test('verified completion removes the loop and notifies without prompting', async (t) => {
  const f = await fixture(t, { ledger: '- [x] First batch — evidence: test command → 12 passed\n' });
  await f.emit();
  assert.equal(await f.exists(), false);
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.notifications.length, 1);
  assert.match(JSON.stringify(f.calls.notifications), /mission done/);
});

test('unchecked evidence remains incomplete', async (t) => {
  const f = await fixture(t, { ledger: '- [x] First batch\n' });
  await f.emit();
  assert.equal(await f.exists(), true);
  assert.equal(f.calls.prompts.length, 1);
});

test('BLOCKED terminates the whole mission', async (t) => {
  const f = await fixture(t, { ledger: '- [ ] First batch\nBLOCKED: First batch — owner approval needed\n' });
  await f.emit();
  assert.equal(await f.exists(), false);
  assert.equal(f.calls.prompts.length, 0);
  assert.match(JSON.stringify(f.calls.notifications), /mission blocked/);
});

test('round cap still stops continuation', async (t) => {
  const f = await fixture(t, { loop: { max_rounds: 1 } });
  await f.emit();
  await f.emit();
  assert.equal(f.calls.prompts.length, 1);
  assert.equal(await f.exists(), false);
  assert.match(JSON.stringify(f.calls.notifications), /mission round cap/);
});

test('two unchanged rounds still stop for no progress', async (t) => {
  const f = await fixture(t);
  await f.emit();
  await f.emit();
  await f.emit();
  assert.equal(f.calls.prompts.length, 2);
  assert.equal(await f.exists(), false);
  assert.match(JSON.stringify(f.calls.notifications), /mission no progress/);
});

test('verified progress resets the stalled-round count', async (t) => {
  const f = await fixture(t);
  await f.emit();
  await f.emit();
  await writeFile(f.ledgerFile, '- [x] First batch — evidence: test → pass\n- [ ] Second batch\n');
  await f.emit();
  assert.equal(f.calls.prompts.length, 3);
  assert.equal(await f.exists(), true);
});

test('overlapping idle events schedule only one continuation', async (t) => {
  let release;
  const held = new Promise((resolve) => { release = resolve; });
  const f = await fixture(t, { holdPrompt: held });
  const first = f.emit();
  while (!f.calls.prompts.length) await new Promise((resolve) => setImmediate(resolve));
  await f.emit();
  release();
  await first;
  assert.equal(f.calls.prompts.length, 1);
});

test('a prompt failure is logged and does not consume a successful round', async (t) => {
  const f = await fixture(t, { loop: { max_rounds: 1 }, promptError: new Error('offline failure') });
  await f.emit();
  await f.emit();
  assert.equal(f.calls.prompts.length, 2);
  assert.equal(await f.exists(), true);
  assert.equal(f.calls.logs.length, 2);
  assert.match(f.calls.logs[0].message, /offline failure/);
});


test('unrelated root cannot claim an unbound loop and logs once', async (t) => {
  const f = await fixture(t, { messages: [{ info: { role: 'assistant', agent: 'build', providerID: 'other', modelID: 'other', time: { created: 3 } } }, ...defaultMessages] });
  const initial = await readFile(f.loopFile, 'utf8');
  await f.emit();
  await f.emit();
  assert.equal(await readFile(f.loopFile, 'utf8'), initial);
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.notifications.length, 0);
  assert.equal(f.calls.logs.length, 1);
  assert.equal(f.calls.logs[0].level, 'warn');
  assert.match(f.calls.logs[0].message, /did not run the mission agent/);
});

test('unrelated root cannot remove a completed unbound loop', async (t) => {
  const f = await fixture(t, { ledger: '- [x] Done — evidence: test → pass\n', messages: [{ info: { role: 'assistant', agent: 'build', providerID: 'other', modelID: 'other', time: { created: 1 } } }] });
  const initial = await readFile(f.loopFile, 'utf8');
  await f.emit();
  assert.equal(await readFile(f.loopFile, 'utf8'), initial);
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.notifications.length, 0);
});

test('bound legacy loop resumes even when the last assistant used build', async (t) => {
  const f = await fixture(t, { loop: { session: 'root' }, messages: [{ info: { role: 'assistant', agent: 'build', providerID: 'legacy', modelID: 'custom', variant: 'medium', time: { created: 1 } } }] });
  await f.emit();
  assert.equal(f.calls.prompts.length, 1);
  assert.equal(f.calls.prompts[0].body.agent, 'mission');
  assert.deepEqual(f.calls.prompts[0].body.model, { providerID: 'legacy', modelID: 'custom' });
  assert.equal(f.calls.prompts[0].body.variant, 'medium');
});


test('round cap persists across plugin reloads', async (t) => {
  const f = await fixture(t, { loop: { max_rounds: 1 } });
  await f.emit();
  assert.deepEqual(JSON.parse(await readFile(f.loopFile, 'utf8')).state, { rounds: 1, previous: 0, stalled: 0 });
  await f.restart();
  await f.emit();
  assert.equal(f.calls.prompts.length, 1);
  assert.equal(await f.exists(), false);
  assert.match(JSON.stringify(f.calls.notifications), /mission round cap/);
});

test('no-progress state persists across plugin reloads', async (t) => {
  const f = await fixture(t);
  await f.emit();
  await f.restart();
  await f.emit();
  assert.deepEqual(JSON.parse(await readFile(f.loopFile, 'utf8')).state, { rounds: 2, previous: 0, stalled: 1 });
  await f.restart();
  await f.emit();
  assert.equal(f.calls.prompts.length, 2);
  assert.equal(await f.exists(), false);
  assert.match(JSON.stringify(f.calls.notifications), /mission no progress/);
});

test('different root sessions cannot schedule the same loop concurrently', async (t) => {
  let release;
  const held = new Promise((resolve) => { release = resolve; });
  const f = await fixture(t, { holdPrompt: held });
  const first = f.emit();
  while (!f.calls.prompts.length) await new Promise((resolve) => setImmediate(resolve));
  await f.emit('other-root');
  assert.equal(f.calls.gets.length, 1);
  release();
  await first;
  assert.equal(f.calls.prompts.length, 1);
  assert.equal(JSON.parse(await readFile(f.loopFile, 'utf8')).session, 'root');
});

for (const [name, ledger] of [['pending', '- [ ] First batch\n'], ['completed', '- [x] First batch — evidence: check → pass\n']]) {
  test(`replacement loop is preserved while checking ownership of an old ${name} loop`, async (t) => {
    let release;
    const held = new Promise((resolve) => { release = resolve; });
    const f = await fixture(t, { ledger, holdMessages: held });
    const first = f.emit();
    while (!f.calls.messages) await new Promise((resolve) => setImmediate(resolve));
    const replacement = JSON.stringify({ ledger: 'other-ledger.md', session: 'new-owner', max_rounds: 8 });
    await writeFile(f.loopFile, replacement);
    release();
    await first;
    assert.equal(await readFile(f.loopFile, 'utf8'), replacement);
    assert.equal(f.calls.prompts.length, 0);
    assert.equal(f.calls.notifications.length, 0);
  });
}

test('replacement loop is not overwritten after asynchronous prompt admission', async (t) => {
  let release;
  const held = new Promise((resolve) => { release = resolve; });
  const f = await fixture(t, { holdPrompt: held });
  const first = f.emit();
  while (!f.calls.prompts.length) await new Promise((resolve) => setImmediate(resolve));
  const replacement = JSON.stringify({ ledger: 'new-ledger.md', session: 'replacement', max_rounds: 4 });
  await writeFile(f.loopFile, replacement);
  release();
  await first;
  assert.equal(await readFile(f.loopFile, 'utf8'), replacement);
});

test('invalid persisted counters cannot bypass the round cap', async (t) => {
  const f = await fixture(t, { loop: { session: 'root', state: { rounds: -1, previous: null, stalled: 0 } } });
  await f.emit();
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(await f.exists(), true);
  assert.match(f.calls.logs[0].message, /invalid round or progress counters/);
});


test('BLOCKED none placeholder does not stop pending work', async (t) => {
  const f = await fixture(t, { ledger: '- [ ] Final audit\n\nBLOCKED: none.\n' });
  await f.emit();
  assert.equal(await f.exists(), true);
  assert.equal(f.calls.prompts.length, 1);
  assert.equal(f.calls.notifications.length, 0);
});

for (const argument of ['help', '--help', '-h']) {
  test(`mission ${argument} leaves an active loop untouched and does not resume it`, async (t) => {
    const f = await fixture(t, { loop: { session: 'root' } });
    const before = await readFile(f.loopFile, 'utf8');
    const output = { parts: [] };
    await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: argument }, output);
    await f.emit();
    assert.equal(await readFile(f.loopFile, 'utf8'), before);
    assert.equal(f.calls.prompts.length, 0);
    assert.equal(f.calls.notifications.length, 0);
    assert.ok(output.parts.some((part) => part.text.includes('HELP.md')));
  });
}

test('a later mission command clears the help-only idle suppression', async (t) => {
  const f = await fixture(t, { loop: { session: 'root' } });
  await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: 'help' }, { parts: [] });
  await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: '/tmp/ledger.md' }, { parts: [] });
  await f.emit();
  assert.equal(f.calls.prompts.length, 1);
});

test('mission setup points the command at SETUP.md and leaves an active loop untouched', async (t) => {
  const f = await fixture(t, { loop: { session: 'root' } });
  const before = await readFile(f.loopFile, 'utf8');
  const output = { parts: [] };
  await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: 'setup' }, output);
  assert.ok(output.parts.some((part) => part.text.includes('SETUP.md')));
  await f.emit();
  assert.equal(await readFile(f.loopFile, 'utf8'), before);
  assert.equal(f.calls.prompts.length, 0);
  assert.equal(f.calls.notifications.length, 0);
});

test('a later mission command clears the setup idle suppression', async (t) => {
  const f = await fixture(t, { loop: { session: 'root' } });
  await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: 'setup' }, { parts: [] });
  await f.plugin['command.execute.before']({ command: 'mission', sessionID: 'root', arguments: '/tmp/ledger.md' }, { parts: [] });
  await f.emit();
  assert.equal(f.calls.prompts.length, 1);
});
