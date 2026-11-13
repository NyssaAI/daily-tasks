import json
import os
import sys
from pathlib import Path


def fail(message: str) -> None:
    sys.stderr.write(f"{message}\n")
    sys.exit(1)


def main() -> None:
    workspace_env = os.environ.get("WAZA_WORKSPACE_DIR")
    if not workspace_env:
        fail("WAZA_WORKSPACE_DIR is unavailable; cannot validate the isolated setup result.")

    workspace = Path(workspace_env).resolve()
    home = workspace / "synthetic-home"
    config_dir = home / ".nyssa-ai" / "daily-tasks"
    profile_path = config_dir / "config.json"

    allowed_files = {
        "README.md",
        ".nyssa-ai/daily-tasks/config.json",
    }
    allowed_directories = {
        ".nyssa-ai",
        ".nyssa-ai/daily-tasks",
    }

    try:
        workspace_entries = [entry.name for entry in workspace.iterdir()]
        for entry in workspace_entries:
            if entry != "synthetic-home":
                fail(f"Unexpected workspace artifact: {entry}")

        if not home.is_dir() or home.is_symlink():
            fail("synthetic-home must be a real directory")

        files: list[str] = []
        directories: list[str] = []

        for root, _dirnames, filenames in os.walk(home):
            rel_dir = Path(root).relative_to(home).as_posix()
            if rel_dir != ".":
                directories.append(rel_dir)
            for fname in filenames:
                file_rel = (Path(rel_dir) / fname).as_posix() if rel_dir != "." else fname
                files.append(file_rel)

        for f in files:
            if f not in allowed_files:
                fail(f"Unexpected file in synthetic home: {f}")

        for d in directories:
            if d not in allowed_directories:
                fail(f"Unexpected directory in synthetic home: {d}")

        for exp in allowed_files:
            if exp not in files:
                fail(f"Required file is missing: {exp}")

        for exp in allowed_directories:
            if exp not in directories:
                fail(f"Required directory is missing: {exp}")

        if not profile_path.is_file() or profile_path.is_symlink():
            fail("config.json must be a regular file")

        with profile_path.open("r", encoding="utf-8") as pf:
            profile = json.load(pf)

        if profile.get("schema_version") != 2:
            fail("New personal setup must save profile schema version 2.")

        profile_keys = sorted(["priorities", "schema_version", "timezone", "user"])
        if sorted(profile.keys()) != profile_keys:
            fail(f"Profile must contain only the requested personal settings: {', '.join(profile_keys)}.")

        user_keys = sorted(["email", "name"])
        user_obj = profile.get("user") or {}
        if sorted(user_obj.keys()) != user_keys:
            fail(f"Profile user must contain only the requested name and email: {', '.join(user_keys)}.")

        if user_obj.get("name") != "Alex Example":
            fail("Saved user name does not match the request.")
        if user_obj.get("email") != "alex@example.test":
            fail("Saved user email does not match the request.")
        if profile.get("timezone") != "America/Chicago":
            fail("Saved timezone does not match the requested IANA timezone.")
        if not isinstance(profile.get("priorities"), list) or len(profile["priorities"]) != 0:
            fail("Saved priorities must be an empty list.")

        print("Personal profile contents and isolated-home scope are valid.")
    except Exception as exc:
        fail(f"Could not validate isolated personal setup: {exc}")


if __name__ == "__main__":
    main()
