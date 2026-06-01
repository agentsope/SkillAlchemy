---
name: nocobase-publish-manage
description: Use when users need NocoBase backup restore or migration publish operations through nb api backup and nb api migration commands.
argument-hint: "[action: plan|run|validate] [method: backup|migration] [source-env=dev] [target-env=dev] [file?] [rule-id?]"
allowed-tools: Bash, Read, Grep, Glob
owner: platform-tools
version: 4.0.0
last-reviewed: 2026-04-30
risk-level: high
---

# Goal

Orchestrate NocoBase backup restore and migration workflows with the current API CLI command surface.

The skill converts user intent into an API-first publish context, carries generated names and local paths between steps, and requires explicit confirmation before restore or migration execution changes target data.

# Scope

- Backup list, create, status, download, remove, restore, restore-upload, and restore-status through `nb api backup`.
- Migration file list, get, create, download, remove, check, and execute through `nb api migration`.
- Migration rule list, get, and global rule create through `nb api migration rules`.
- Migration log list, get, and download through `nb api migration logs` for diagnosis.
- Same-environment and cross-environment workflows. The default test workflow uses `source_env=dev` and `target_env=dev`.
- Planning, dry explanation, read-only validation, and failure diagnosis from command output.

# Non-Goals

- This skill focuses on the API CLI command surface listed in Scope.
- Package and rule selection stays explicit.
- Restore, execute, and remove actions stay behind the execution confirmation gate.
- Failure recovery preserves the current context and waits for user direction before a new package or rule is created.

# Input Contract

| Input | Required | Default | Validation | Clarification |
|---|---|---|---|---|
| `action` | yes | inferred | `plan`, `run`, or `validate` | "Should I plan, run, or validate the workflow?" |
| `method` | run: yes | inferred | `backup` or `migration` | "Use backup restore or migration publish?" |
| `source_env` | conditional | `dev` for tests | non-empty env name | "Which environment provides or generates the file?" |
| `target_env` | run: yes | `dev` for tests | non-empty env name | "Which environment should receive and execute the file?" |
| `backup_name` | optional | unset | backup file name from `backup list/create` | "Which server backup should be restored or downloaded?" |
| `migration_name` | optional | unset | migration file name from `migration list/create` | "Which server migration package should be downloaded?" |
| `local_file` | optional | unset | readable local `.nbdata` path | "Which local package file should be uploaded or executed?" |
| `cli_home` | optional | CLI global home | writable CLI home directory | "Which CLI home should store downloaded release files?" |
| `rule_id` | migration create only | unset | non-empty id | "Which migration rule ID should be used?" |
| `migration_user_rule` | migration rule create only | `schema-only` | `schema-only` or `overwrite` | "How should user-defined tables be handled?" |
| `migration_system_rule` | migration rule create only | `overwrite-first` | `overwrite-first` or `schema-only` | "How should system tables be handled?" |
| `title` | migration create only | `publish-<source>-to-<target>` | non-empty text | "Which migration title should be used?" |
| `execute_options` | optional | safe CLI defaults | known `nb api backup restore*` or `nb api migration execute` flags | "Any high-risk flags such as `--skip-backup` or `--skip-revert-on-error`?" |
| `confirm_publish_input` | before create/download/rule create/check | unset | explicit approval | "Confirm the selected input before I create, download, or check the package." |
| `confirm_execute` | before restore/execute/remove | unset | must be `confirm` | "Type `confirm` to execute on the target environment." |

# Mandatory Clarification Gate

- Max clarification rounds: 2.
- Ask at most 3 short questions per round.
- Mutation steps require resolved `method`, `source_env`, and `target_env`.
- Migration package creation requires a selected or newly created `rule_id`.
- Existing package list flows require user selection of a specific file.
- Package create, package download, migration rule create, and migration check require publish input confirmation.
- Backup restore, backup restore-upload, backup remove, migration execute, and migration remove require execution confirmation.
- If the user says "you decide", choose a read-only planning path.

# Workflow

1. Route intent to `backup` or `migration`.
2. Build a context with `method`, `sourceEnv`, `targetEnv`, `cliHome`, `releaseDir`, `backupName`, `migrationName`, `localFile`, `downloadPath`, `ruleId`, `title`, and `step`.
3. Run read-only capability probes for the needed command groups. Treat 404, `Not Found`, unknown resource, inactive plugin, or license capability errors as `unsupported_publish_env`.
4. For backup restore:
   - Local file: confirm the file, then restore it with `nb api backup restore-upload --file <localFile> -e <targetEnv> --force`.
   - Server backup on target: confirm the backup name, then restore it with `nb api backup restore --name <backupName> -e <targetEnv> --force`.
   - Source-to-target: create or select the backup on `sourceEnv`, download it to `<cliHome>/release/<sourceEnv>/<backupName>`, then restore-upload that path on `targetEnv` with `--force`.
5. For migration:
   - Local file: confirm the file, check it on `targetEnv`, then execute it on `targetEnv`.
   - Server migration package: download it from `sourceEnv` to `<cliHome>/release/<sourceEnv>/<migrationName>`, check it on `targetEnv`, then execute it on `targetEnv`.
   - Created migration package: list or create a global rule, create the migration on `sourceEnv`, poll `migration get` until the generated package reports `status=ok`, download it to `<cliHome>/release/<sourceEnv>/<migrationName>`, check it on `targetEnv`, then execute it on `targetEnv`.
6. Poll or inspect status with available commands when needed: `backup status`, `backup restore-status --task <taskId>`, `migration get`, and `migration logs`.
7. Treat restore task ids as compatible fields: parse `taskId` from `data.taskId` or `data.task`, then pass that value to `backup restore-status --task`.
8. Report the final state, commands executed or planned, file names, local paths, failed step, and next verification command.

See [Runtime Contract](references/v1-runtime-contract.md) for exact command construction and parsing rules.

# Reference Loading Map

| Reference | Use When |
|---|---|
| [Intent Routing](references/intent-routing.md) | Mapping user phrases to backup, migration, file reuse, and environment shape. |
| [Runtime Contract](references/v1-runtime-contract.md) | Building commands and carrying names, paths, rules, and status between steps. |
| [Test Playbook](references/test-playbook.md) | Validating supported API workflows and failure cases. |

# Safety Gate

High-impact actions:

- `nb api backup restore`
- `nb api backup restore-upload`
- `nb api backup remove`
- `nb api migration execute`
- `nb api migration remove`
- `nb api migration rules create`
- any option that skips target backup or revert behavior, such as `--skip-backup` or `--skip-revert-on-error`

Publish input confirmation template:

```text
Confirm publish input: <method> from <source_env> to <target_env>. Package source: <existing server file | local file | create new>. Migration rule: <ruleId/name | create new with user-defined-rule/system-defined-rule | not applicable>. Reply `confirm input` to continue with package creation, download, or check.
```

Execution confirmation template:

```text
Confirm execution: <backup restore | migration execute> on <target_env> using <backupName | migrationName | localFile>. This may change target data. Reply `confirm` to continue.
```

Failure guidance:

- Backup restore failure: if a restore task id is available from `data.taskId` or `data.task`, inspect `nb api backup restore-status --task <taskId> -e <targetEnv>`.
- Migration package creation: if `migration get` reports `status=in_progress`, tell the user the package is still generating, wait, and do not run `migration download` until `status=ok`.
- Migration check failure: report the check output and keep the local package path.
- Migration execution failure: inspect `nb api migration logs list -e <targetEnv>` and relevant `logs get/download` output.
- Package or rule recreation after a failure requires explicit user instruction.
- Preserve the context in the final response so the user can resume from the correct file or rule.

# Verification Checklist

- Publish operations use `nb api backup` and `nb api migration` command groups.
- The default test context is `sourceEnv=dev` and `targetEnv=dev`.
- Participating environments pass read-only command probes before mutation.
- Capability probe failures are reported as `unsupported_publish_env`.
- Package lists and migration rule lists lead to explicit user selection.
- Existing local files skip package creation.
- Existing server backup names may use `backup restore --name` when restoring inside the same target environment.
- Cross-environment backup restore uses `backup download` followed by `backup restore-upload --force`.
- Backup restore and restore-upload commands include `--force` directly.
- Downloaded backup, migration, and log files are stored under `<cliHome>/release/<sourceEnv>/`.
- Migration execution uses a local package file with `migration check --file` before `migration execute --file`.
- Missing migration file triggers migration rule list before asking for or creating `rule_id`.
- `migration rules create` uses global rule options.
- Created or selected migration rules are verified with `migration rules get` when possible.
- Download commands include `--output`.
- Restore status commands include `--task <taskId>` and are only run after a task id is returned as `data.taskId` or `data.task`.
- Restore or execute waits for secondary confirmation.
- Failure output includes the failed step and relevant CLI lines.

# References

- [Intent Routing](references/intent-routing.md)
- [Runtime Contract](references/v1-runtime-contract.md)
- [Test Playbook](references/test-playbook.md)
- [NocoBase Migration Manager](https://docs.nocobase.com/ops-management/migration-manager/): official context for migration risk and publish-related operations. [verified: 2026-04-30]
