---
name: readme-i18n
description: Use when the user wants to translate a repository README, make a repo multilingual, localize docs, add a language switcher, internationalize the README, or update localized README variants in a GitHub-style repository.
---

Localize a repository `README.md` without breaking the repo mechanics around it.

The default job is translate + wire-up:

- read the source-of-truth README
- create localized sibling files such as `README.zh.md`
- preserve GitHub-flavored Markdown structure and repo-specific tokens
- add or update a shared language selector near the top of every variant

This skill is for multilingual README workflows, not general website/app i18n.

## Inputs

Expect these inputs when available:

- source README path, default `README.md`
- source language, default inferred or English
- one or more target languages
- optional glossary or do-not-translate list
- optional filename override if the repo already uses a different multilingual naming pattern

If target languages are not named, inspect existing translated files, selectors, filenames, issues, or prior repo conventions. If that still leaves the target languages unclear, ask once. Do not invent target languages.

## Defaults And Decision Rules

- Treat the root `README.md` as the source-of-truth unless the user explicitly says otherwise.
- If the source language is ambiguous, ask once. Otherwise assume English.
- Keep section order aligned with the source README. Only make a small heading wording adjustment when needed to produce a valid localized anchor.
- Output localized siblings with `README.<bcp47-tag>.md` naming unless the repo already has a different established pattern that should be preserved.
- Update an existing language selector in place. Do not duplicate it.
- Translate only human-language content.
- Preserve project names, package names, commands, CLI flags, option names, environment variables, URLs, file paths, inline code, code fences, HTML attributes, and badge/image URLs.
- Badge alt text or visible labels may be translated only when the change does not require changing the badge URL, query params, or image source.
- If a glossary or do-not-translate list is provided, apply it consistently across every target language.

## Workflow

### 1. Establish the source README and languages

- Confirm the source README path. Default to `README.md`.
- Identify the source language from the file contents and repo context.
- Determine target languages from the request or existing repo pattern.
- Note any glossary terms, product names, or phrases that must stay untranslated.

### 2. Audit the Markdown structure before translating

Read the source README once as structure, not prose. Open [`references/preservation-checklist.md`](./references/preservation-checklist.md) and inventory the elements most likely to break:

- headings and heading levels
- badge rows, shields URLs, and image links
- tables and alignment rows
- raw HTML blocks and inline HTML
- GitHub alerts or admonitions such as `> [!NOTE]`
- code fences, inline code, commands, and config snippets
- intra-document anchors such as `(#installation)`
- relative links to files, docs, screenshots, or other README variants

If the README already has localized siblings, inspect them too before choosing filenames or selector style.

### 3. Translate only the prose layer

Translate:

- paragraph text
- list item prose
- table cell prose
- visible text inside HTML blocks
- image alt text when safe
- selector labels and other human-facing labels

Do not translate:

- fenced code blocks
- inline code spans
- shell commands
- flags such as `--help`
- env vars such as `OPENAI_API_KEY`
- URLs
- file paths
- repo/package/project identifiers
- badge and image URLs

When in doubt, preserve the literal token and translate the surrounding sentence instead.

### 4. Preserve structure while writing the localized README

- Keep the same heading hierarchy and section order as the source.
- Keep the same number of code fences unless the user explicitly asks to rewrite examples.
- Preserve table shape, list nesting, HTML wrappers, and Markdown comments.
- Preserve relative links unless a link intentionally needs to point at a localized sibling README.

### 5. Rewrite localized anchors and anchor-dependent links

When a translated heading changes, GitHub will generate a different heading ID. After translating headings:

- rewrite every same-file `(#...)` link so it matches the localized heading slug in that file
- preserve custom explicit anchors such as `<a id="...">` unless the file already uses localized explicit IDs
- verify that every intra-document anchor target resolves to an existing heading or explicit anchor

Prefer a small heading wording adjustment over a broken anchor. The section order should still match the source README.

### 6. Write sibling files using the repo's naming pattern

Default to sibling filenames like:

- `README.zh.md`
- `README.es.md`
- `README.fr.md`

If the repo already uses a different multilingual naming pattern, keep using it consistently rather than forcing the default pattern.

### 7. Insert or update the language selector

Open [`references/language-selector-reference.md`](./references/language-selector-reference.md) before editing selectors.

Placement:

- keep the selector near the top of the file
- if the README starts with a title, badges, hero image, or short intro block, place the selector immediately after that opening cluster

Behavior:

- update an existing selector block in place if one already exists
- if you add a new selector, use the canonical marker comments from the reference file so later runs can update it deterministically
- emphasize the current language and link the other variants
- keep selector order and labels consistent across every README variant

### 8. Final verification

Before finishing, verify:

- localized filenames follow the chosen pattern
- every README variant contains exactly one selector block
- code fence counts are preserved
- badge/image URLs and relative file links still point to the original targets unless intentionally localized
- every `(#...)` link resolves inside its own file
- the localized README still feels structurally identical to the source

## Output

Produce:

- one localized sibling README per target language
- an updated selector block in every README variant
- a brief note to the user covering created or updated files, any assumptions, and any terms intentionally left untranslated

## Maintenance Note

Keep `README.md` as the canonical source unless the user says otherwise. When the source README changes later, update each localized sibling by diffing the changed prose, then re-check selectors, filenames, and anchor links instead of reformatting the whole file from scratch.

## Example Prompts

**Example 1**

`Translate this README into Chinese and add a language switcher. Keep badge URLs, code fences, and all commands exactly as they are.`

**Example 2**

`Make the repo multilingual. Add Spanish and Chinese README variants, keep the internal anchor links working, and wire the selector into every file.`

**Example 3**

`We already have README.zh.md. Add README.es.md and update the existing selector in place instead of adding a second one.`

## Common Mistakes

- Translating fenced code blocks or inline code instead of only the prose around them
- Duplicating the language selector instead of updating the existing block
- Translating a heading but forgetting to rewrite same-file `(#...)` links
- Changing badge URLs or image sources while trying to translate visible labels
- Reordering sections in the localized README even though the source README is the authority
