---
name: obsidian-cli
description: Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and more. Also supports plugin and theme development with commands to reload plugins, run JavaScript, capture errors, take screenshots, and inspect the DOM. Use when the user asks to interact with their Obsidian vault, manage notes, search vault content, perform vault operations from the command line, or develop and debug Obsidian plugins and themes.
---

# Obsidian CLI

Use the `obsidian` CLI to interact with a running Obsidian instance. Requires Obsidian to be open.

## Command reference

Run `obsidian help` to see all available commands. This is always up to date. Full docs: https://help.obsidian.md/cli

## Syntax

**Parameters** take a value with `=`. Quote values with spaces:

```bash
obsidian create name="My Note" content="Hello world"
```

**Flags** are boolean switches with no value:

```bash
obsidian create name="My Note" silent overwrite
```

For multiline content use `\n` for newline and `\t` for tab.

## File targeting

Many commands accept `file` or `path` to target a file. Without either, the active file is used.

- `file=<name>` — resolves like a wikilink (name only, no path or extension needed)
- `path=<path>` — exact path from vault root, e.g. `folder/note.md`

## Vault targeting

Commands target the most recently focused vault by default. Use `vault=<name>` as the first parameter to target a specific vault:

```bash
obsidian vault="My Vault" search query="test"
```

## Common patterns

```bash
obsidian read file="My Note"
obsidian create name="New Note" content="# Hello" template="Template" silent
obsidian append file="My Note" content="New line"
obsidian search query="search term" limit=10
obsidian tasks daily todo
obsidian files ext=md | grep "$(date +%F)"   # resolve today's daily note
obsidian property:set name="status" value="done" file="My Note"
obsidian tasks daily todo
obsidian tags sort=count counts
obsidian backlinks file="My Note"
```

Use `--copy` on any command to copy output to clipboard. Use `silent` to prevent files from opening. Use `total` on list commands to get a count.

## Verified command surface (CLI 1.14.5, checked 2026-10-25)

This skill's examples are verified against **Obsidian CLI 1.14.5** (installer 1.12.7).

**These command families do NOT exist in this build.** Probing them returns
`No commands matching "..."`. Report the gap — never simulate success output.

| Family | Probe | Substitute |
|---|---|---|
| `daily` / `daily:path` / `daily:read` / `daily:append` | `obsidian help daily:read` | resolve the path manually: `obsidian files ext=md \| grep "<YYYY-MM-DD>"`, then use `path=` |
| `sync` / `sync:status` / `sync:history` / `sync:read` / `sync:restore` / `sync:deleted` | `obsidian help sync:status` | local history only: `history` / `history:list` / `history:read` / `diff` / `history:restore` |
| `publish:site` / `publish:list` / `publish:status` / `publish:add` / `publish:remove` | `obsidian help publish:status` | none — Publish is unavailable |
| `workspace:save` / `workspace:load` / `workspace:delete` | `obsidian help workspace:load` | read-only `workspace` only; layout switching is a UI action |
| `web` | `obsidian help web` | open in the system browser |
| `unique` | `obsidian help unique` | `create name=...` (auto-uniquifies) then `rename` |
| `vault:open` | `obsidian help vault:open` | `vault` / `vaults` are read-only |

**Re-probe after every Obsidian CLI upgrade** — the surface area can change.

## Plugin development

### Develop/test cycle

After making code changes to a plugin or theme, follow this workflow:

1. **Reload** the plugin to pick up changes:
   ```bash
   obsidian plugin:reload id=my-plugin
   ```
2. **Check for errors** — if errors appear, fix and repeat from step 1:
   ```bash
   obsidian dev:errors
   ```
3. **Verify visually** with a screenshot or DOM inspection:
   ```bash
   obsidian dev:screenshot path=screenshot.png
   obsidian dev:dom selector=".workspace-leaf" text
   ```
4. **Check console output** for warnings or unexpected logs:
   ```bash
   obsidian dev:console level=error
   ```

### Additional developer commands

Run JavaScript in the app context:

```bash
obsidian eval code="app.vault.getFiles().length"
```

Inspect CSS values:

```bash
obsidian dev:css selector=".workspace-leaf" prop=background-color
```

Toggle mobile emulation:

```bash
obsidian dev:mobile on
```

Run `obsidian help` to see additional developer commands including CDP and debugger controls.
