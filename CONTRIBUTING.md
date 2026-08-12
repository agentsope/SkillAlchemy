# Contributing

SkillAlchemy is an open-world agent skill creation system built from three
markdown-based Skills. Contributions are welcome.

## What can be contributed

- **Domain packs** (`skills/LEAP/domains/`): Add or improve domain reference packs
- **Skill grammar**: Improve presentation patterns using evidence from public Skills
- **Exemplar scoring**: Refine the mechanical rubric used by `score_skill.py`
- **Method implementation**: Improve evidence acquisition, procedure admission, or compilation
- **Documentation**: Improve the README or technical overview

## How to contribute

1. Fork the repository
2. Make your changes
3. Run the checks below
4. Submit a pull request with a clear description

```bash
python3 -m py_compile skills/LEAP/scripts/*.py
python3 skills/LEAP/scripts/score_skill.py --skill SKILL.md --json
python3 skills/LEAP/scripts/score_skill.py --skill skills/Lens/SKILL.md --json
python3 skills/LEAP/scripts/score_skill.py --skill skills/LEAP/SKILL.md --json
```

## Code style

- `SKILL.md` files follow the [skill grammar](skills/LEAP/references/skill-grammar.md)
- Python scripts use standard library only, no external dependencies
- All files are UTF-8 encoded

## License

MIT — contributions are under the same license.
