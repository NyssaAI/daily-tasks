from pathlib import Path

def register(ctx):
    for skill in sorted((Path(__file__).resolve().parent / "skills").glob("*/SKILL.md")):
        ctx.register_skill(skill.parent.name, skill)
