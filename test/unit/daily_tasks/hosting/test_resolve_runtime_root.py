"""Responsibility: Verify the 4-step deterministic runtime_root resolution chain and agent persona detection.
Public interface:
+-- test_is_agent_runtime_root_requires_both_soul_and_identity(tmp_path)
+-- test_resolve_runtime_root_four_step_precedence_chain(tmp_path)
+-- test_resolve_runtime_root_rejects_relative_paths()
+-- test_resolve_runtime_root_step2_routes_agent_persona_env_to_runtime_subdir(tmp_path)
`-- test_resolve_runtime_root_step4_repo_root_fallback_before_user_config_dir(tmp_path)

Unit tests for `is_agent_runtime_root` and `resolve_runtime_root`.
"""

from pathlib import Path

from nyssa_ai_result import Err, Ok

from daily_tasks.hosting import RUNTIME_ROOT_ENV_VAR, is_agent_runtime_root, resolve_runtime_root


def test_is_agent_runtime_root_requires_both_soul_and_identity(tmp_path: Path) -> None:
    assert not is_agent_runtime_root(tmp_path)

    (tmp_path / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    assert not is_agent_runtime_root(tmp_path)

    (tmp_path / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")
    assert is_agent_runtime_root(tmp_path)


def test_resolve_runtime_root_four_step_precedence_chain(tmp_path: Path) -> None:
    explicit_rt = tmp_path / "explicit-rt"
    env_rt = tmp_path / "env-rt"
    persona_cwd = tmp_path / "agent-work" / "hermes" / "nyssa"
    persona_cwd.mkdir(parents=True)
    (persona_cwd / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (persona_cwd / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")
    normal_cwd = tmp_path / "normal-cwd"
    normal_cwd.mkdir()
    configured_rt = tmp_path / "configured-rt"
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"

    # Step 1: Explicit --runtime-root wins over everything
    step1 = resolve_runtime_root(
        explicit=explicit_rt,
        environ={RUNTIME_ROOT_ENV_VAR: str(env_rt)},
        cwd=persona_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
    )
    assert isinstance(step1, Ok) and step1.value == explicit_rt.resolve()

    # Step 2: NYSSA_RUNTIME_ROOT env var wins over persona cwd, configured runtimeRoot, and default
    step2 = resolve_runtime_root(
        explicit=None,
        environ={RUNTIME_ROOT_ENV_VAR: str(env_rt)},
        cwd=persona_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
    )
    assert isinstance(step2, Ok) and step2.value == env_rt.resolve()

    # Step 3: Agent runtime root cwd (SOUL.md + IDENTITY.md) routes to <cwd>/.nyssa-ai/daily-tasks/runtime
    step3 = resolve_runtime_root(
        explicit=None,
        environ={},
        cwd=persona_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
    )
    assert isinstance(step3, Ok)
    assert step3.value == (persona_cwd / ".nyssa-ai" / "daily-tasks" / "runtime").resolve()

    # Step 4a: Configured runtimeRoot in config.json wins over repo_root and default <config_dir>/runtime
    step4a = resolve_runtime_root(
        explicit=None,
        environ={},
        cwd=normal_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
    )
    assert isinstance(step4a, Ok) and step4a.value == configured_rt.resolve()

    # Step 4b: Default falls back to <config_dir>/runtime
    step4b = resolve_runtime_root(
        explicit=None,
        environ={},
        cwd=normal_cwd,
        configured=None,
        config_dir=config_dir,
    )
    assert isinstance(step4b, Ok) and step4b.value == (config_dir / "runtime").resolve()


def test_resolve_runtime_root_step2_routes_agent_persona_env_to_runtime_subdir(tmp_path: Path) -> None:
    persona_env = tmp_path / "agent-work" / "hermes" / "nyssa"
    persona_env.mkdir(parents=True)
    (persona_env / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (persona_env / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")
    plain_env = tmp_path / "plain-env-runtime"
    plain_env.mkdir(parents=True)

    persona_res = resolve_runtime_root(
        environ={RUNTIME_ROOT_ENV_VAR: str(persona_env)},
        cwd=tmp_path,
        config_dir=tmp_path / "config",
    )
    assert isinstance(persona_res, Ok)
    assert persona_res.value == (persona_env / ".nyssa-ai" / "daily-tasks" / "runtime").resolve()

    plain_res = resolve_runtime_root(
        environ={RUNTIME_ROOT_ENV_VAR: str(plain_env)},
        cwd=tmp_path,
        config_dir=tmp_path / "config",
    )
    assert isinstance(plain_res, Ok)
    assert plain_res.value == plain_env.resolve()


def test_resolve_runtime_root_step4_repo_root_fallback_before_user_config_dir(tmp_path: Path) -> None:
    normal_cwd = tmp_path / "normal-cwd"
    normal_cwd.mkdir()
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    configured_rt = tmp_path / "configured-rt"

    # When <repo_root>/.nyssa-ai/daily-tasks does not exist yet, falls through to <config_dir>/runtime
    without_repo_app_dir = resolve_runtime_root(
        environ={},
        cwd=normal_cwd,
        configured=None,
        config_dir=config_dir,
        repo_root=repo_root,
    )
    assert isinstance(without_repo_app_dir, Ok)
    assert without_repo_app_dir.value == (config_dir / "runtime").resolve()

    # When <repo_root>/.nyssa-ai/daily-tasks exists, resolves <repo_root>/.nyssa-ai/daily-tasks/runtime
    (repo_root / ".nyssa-ai" / "daily-tasks").mkdir(parents=True)
    with_repo_app_dir = resolve_runtime_root(
        environ={},
        cwd=normal_cwd,
        configured=None,
        config_dir=config_dir,
        repo_root=repo_root,
    )
    assert isinstance(with_repo_app_dir, Ok)
    assert with_repo_app_dir.value == (repo_root / ".nyssa-ai" / "daily-tasks" / "runtime").resolve()

    # Configured runtimeRoot still takes precedence over <repo_root>/.nyssa-ai/daily-tasks/runtime
    configured_wins = resolve_runtime_root(
        environ={},
        cwd=normal_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
        repo_root=repo_root,
    )
    assert isinstance(configured_wins, Ok)
    assert configured_wins.value == configured_rt.resolve()


def test_resolve_runtime_root_rejects_relative_paths() -> None:
    rel_explicit = resolve_runtime_root(explicit=Path("relative/runtime"))
    assert isinstance(rel_explicit, Err) and "--runtime-root" in rel_explicit.message

    rel_env = resolve_runtime_root(environ={RUNTIME_ROOT_ENV_VAR: "relative/env"})
    assert isinstance(rel_env, Err) and RUNTIME_ROOT_ENV_VAR in rel_env.message

    rel_cfg = resolve_runtime_root(environ={}, cwd=Path("/tmp"), configured="relative/cfg")
    assert isinstance(rel_cfg, Err) and "runtimeRoot" in rel_cfg.message
