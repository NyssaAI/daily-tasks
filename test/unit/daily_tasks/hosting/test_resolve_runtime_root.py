"""Responsibility: Verify the 4-step deterministic runtime_root resolution chain and agent persona detection.
Public interface:
+-- test_is_agent_runtime_root_requires_both_soul_and_identity(tmp_path)
+-- test_resolve_runtime_root_four_step_precedence_chain(tmp_path)
`-- test_resolve_runtime_root_rejects_relative_paths()

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

    # Step 3: Agent runtime root cwd (SOUL.md + IDENTITY.md) wins over configured runtimeRoot and default
    step3 = resolve_runtime_root(
        explicit=None,
        environ={},
        cwd=persona_cwd,
        configured=str(configured_rt),
        config_dir=config_dir,
    )
    assert isinstance(step3, Ok) and step3.value == persona_cwd.resolve()

    # Step 4a: Configured runtimeRoot in profile.json wins over default <config_dir>/runtime
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


def test_resolve_runtime_root_rejects_relative_paths() -> None:
    rel_explicit = resolve_runtime_root(explicit=Path("relative/runtime"))
    assert isinstance(rel_explicit, Err) and "--runtime-root" in rel_explicit.message

    rel_env = resolve_runtime_root(environ={RUNTIME_ROOT_ENV_VAR: "relative/env"})
    assert isinstance(rel_env, Err) and RUNTIME_ROOT_ENV_VAR in rel_env.message

    rel_cfg = resolve_runtime_root(environ={}, cwd=Path("/tmp"), configured="relative/cfg")
    assert isinstance(rel_cfg, Err) and "runtimeRoot" in rel_cfg.message
