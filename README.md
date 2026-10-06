# /defuse

Turn a dense document into an offline HTML reader with a full original, a clear summary, source links, examples, and comments.

## Install in Claude Code

As a plugin, which you can update through `/plugin`:

```text
/plugin marketplace add marcammann/defuse-skill
/plugin install defuse@defuse
```

The plugin answers to `/defuse:defuse`.

As a personal skill, which answers to `/defuse`:

```bash
git clone https://github.com/marcammann/defuse-skill.git ~/.claude/skills/defuse
```

If you set `CLAUDE_CONFIG_DIR`, clone into its `skills` folder instead. For one project only, clone into `.claude/skills/defuse` in that project. Update with `git pull` in the cloned folder, then start a new session.

## Install in Codex

```bash
git clone https://github.com/marcammann/defuse-skill.git ~/.codex/skills/defuse
```

If you use a custom `CODEX_HOME`, clone into its `skills` folder. Start a new chat, attach or identify a document, and ask: "Use $defuse to turn this document into a readable HTML reader." Update with `git pull` in the cloned folder.

Only Codex reads `agents/openai.yaml`, and only Claude Code reads `.claude-plugin/`. The same repository works in both agents.

## Requirements

The agent needs a local Python 3 runtime to run the renderer. The Markdown parser is bundled; no pip install or CDN is needed. Open the resulting HTML in a modern browser. JavaScript enables comments, linked scrolling, progress, and quick navigation; the text remains readable without it.

Helvetica Now is used when locally installed. Font files are not included. System fonts provide the fallback.

## Outputs and notes

The skill saves a `.defused.html` reader and an editable `.defused.json` file beside the source when writable, otherwise in the task workspace. You can request a different destination.

Select text and type to comment. Enter saves; Shift+Enter inserts a new line. Comments stay in the browser's local storage, separately from the HTML. Use Export and Import to keep or transfer notes. Sharing the HTML does not share saved comments.

The repository contains the reusable skill only, with no personal source documents, generated summaries, or saved comments.

## Included dependencies

Mistune 3.0.2 is distributed under the BSD-3-Clause license. Its notice and license are included in `scripts/_vendor/`.

The writing pass uses the instructions from humanizer 3.0.0 by Siqi Chen, copied into `references/humanizer.md` under the MIT license in `references/humanizer-LICENSE.txt`. The humanizer skill does not need to be installed.

## License

MIT, see `LICENSE`. The included Mistune and humanizer files keep their own licenses, listed above.
