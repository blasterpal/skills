# Configuring conversation folders

The helper's `setup` command writes `${XDG_CONFIG_HOME:-~/.config}/convo/config.json`; nobody needs to edit the JSON by hand. A preload for `setup` prints `CONFIG_FILE=` and the current `CONFIG=` JSON; a preload with `SETUP_REQUIRED=` means the selected profile has no folder yet.

## One folder

Most people need one conversation folder. Ask where to keep it, suggesting a context directory for persistent notes such as `~/context` with conversations in `~/context/convos`, and say that the chosen path is the conversation folder itself. Wait for the answer; the suggestion is not consent to create it. Then run:

```sh
python3 <skill-directory>/scripts/convo.py setup --root '<chosen-conversation-folder>'
```

This creates the folder and writes `{"profiles": {"me": "<folder>"}}`. Resume the original request afterwards. Changing a folder later with the same command does not move existing snapshots; say so if asked to change one.

## Several folders

Each conversation folder is a profile. Add one with `--profile <name>` and any options, repeating `--alias`, `--dir`, and `--env` as needed:

```sh
python3 <skill-directory>/scripts/convo.py --profile work setup --root ~/work-notes/convos \
  --alias w --dir ~/work-notes --dir ~/code/work-repo \
  --instructions ~/work-notes/convos/CONVO.md --save-hook ~/bin/convo-work-hook \
  --default --env MY_DOMAIN
```

| Option | Config key | Effect |
|---|---|---|
| `--root` | `root` | The conversation folder. Required the first time a profile is set up. |
| `--alias` | `aliases` | Another name, accepted before or after the verb (`/convo w recent`) and in refs (`w:convos/2026-10/<file>.md`). An alias may not already name another profile. |
| `--dir` | `dirs` | A working directory, including its subfolders, that selects this profile when nothing else does. |
| `--base` | `base` | Folder that `<alias>:path` and `convos/...` refs are relative to. The root's parent by default. |
| `--instructions` | `instructions` | Markdown appended to every preload for this profile. `<root>/CONVO.md` is used automatically when present, so this is only for a file elsewhere. |
| `--save-hook` | `save_hook` | Shell command run during a save preload with `CONVO_ROOT` and `CONVO_PROFILE` set, 15 second limit. Its stdout joins the save metadata; a failure appears as `SAVE_HOOK_FAILED=`. |
| `--default` | top-level `default` | Makes this profile the one used when nothing else selects one. `me` when unset. |
| `--env` | top-level `profile_env` | An environment variable whose value names a profile or alias. `CONVO_PROFILE` is always checked first. |

Options on an existing profile merge: `--root` replaces the folder and keeps the other keys, `--alias` and `--dir` append. `setup` with no options prints the selected profile's settings, the config file path, and the profile names.

## How a profile is selected

In order: `--profile <name>` on the command line, then `CONVO_PROFILE` and the `profile_env` variables, then the profile whose `dirs` contain the working directory (the deepest match wins), then `default`, then `me`. A configured profile name or alias before the verb or right after it selects the profile for one request; any other word belongs to the topic. Once a request names a profile, pass `--profile <name>` on every follow-up helper call and stay there until the user selects another.

## Instructions file

Put conventions that apply only to one folder in its instructions file, for example where memos go, how to link a task tracker, what metadata to add, or which other profile's material must not be copied in. The preload appends it after the reference file, and it takes precedence over the reference where they differ. Keep it short; it is read on every request.
