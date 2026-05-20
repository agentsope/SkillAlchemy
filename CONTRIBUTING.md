# Contributing

Skill-Alchemy is a Skill production operating system — a set of three markdown-based Skills that work together. Contributions are welcome.

## What can be contributed

- **Domain packs** (`LEAP/domains/`): Add or improve domain reference packs for research dimension selection
- **skill-grammar refinements**: Improve the writing methodology with new data from skills.sh
- **score_skill improvements**: Refine the 13-point scoring rubric
- **Bug fixes**: Pipeline logic, quality checks, script fixes
- **Documentation**: README, technical docs, translations

## How to contribute

1. Fork the repository
2. Make your changes
3. Run `python3 LEAP/scripts/quality_check.py` and `python3 LEAP/scripts/score_skill.py` to verify
4. Submit a pull request with a clear description

## Code style

- SKILL.md files follow the [skill-grammar](LEAP/references/skill-grammar.md) conventions
- Python scripts use standard library only, no external dependencies
- All files are UTF-8 encoded

## License

MIT — contributions are under the same license.
