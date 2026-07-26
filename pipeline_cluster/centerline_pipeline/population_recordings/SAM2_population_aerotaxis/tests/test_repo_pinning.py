#!/usr/bin/env python3
"""
Tests that a run uses YOUR clone's analysis package, not a copy installed in the
conda env.

Why this matters: the Snakefile's rules `import centerline_behavior_annotation`.
Python resolves that from sys.path, so on the lab cluster it lands on the SHARED
checkout even when the Snakefile, the config and every script came from a
personal clone. A fix made in the clone then does nothing, silently -- which is
exactly what happened to the centerline/curvature fixes for the 4,576-crop run.

The Snakefile is not importable (it contains `rule` blocks), so these tests exec
its header -- the real code, not a copy of it -- against a stub `config` and a
fake "installed" package planted on sys.path.

Run:  pytest test_repo_pinning.py -q
"""
import contextlib
import io
import sys
import types
from pathlib import Path

import pytest
import yaml

_HERE = Path(__file__).resolve().parent
_SNAKEDIR = _HERE.parent / "snakemake_files" / "snakefiles_aerotaxis"
_SNAKEFILE = _SNAKEDIR / "Snakefile"
_CONFIG = _SNAKEDIR / "config.yaml"
_REPO_ROOT = _HERE.parents[4]

PKG = "centerline_behavior_annotation"


def _snakefile_header():
    """Everything above the first rule -- the part that runs at DAG build."""
    return _SNAKEFILE.read_text().split("\nrule all:")[0]


def _stub_snakemake():
    io_m = types.ModuleType("snakemake.io")
    io_m.glob_wildcards = lambda *a, **k: None
    io_m.temp = lambda x: x
    io_m.touch = lambda x: x
    exc = types.ModuleType("snakemake.exceptions")

    class WorkflowError(Exception):
        pass

    exc.WorkflowError = WorkflowError
    sys.modules.setdefault("snakemake", types.ModuleType("snakemake"))
    sys.modules["snakemake.io"] = io_m
    sys.modules["snakemake.exceptions"] = exc


def _fake_installed_package(tmp_path):
    """A stand-in for the shared lab checkout already importable in the env."""
    root = tmp_path / "fake_env_site_packages"
    (root / PKG).mkdir(parents=True)
    (root / PKG / "__init__.py").write_text("")
    return root


@pytest.fixture
def clean_imports():
    """
    Isolate sys.path / sys.modules per test.

    Evicts on the way IN as well as out: sibling test modules import the package
    at collection time, so without this a test's "the shared copy is imported
    first" precondition would silently already hold for the clone instead.
    """
    saved_path = list(sys.path)
    saved_mods = {k: v for k, v in sys.modules.items() if k.startswith(PKG)}
    for k in list(saved_mods):
        del sys.modules[k]
    # Also drop the repo root so a fake "installed" copy can genuinely win.
    sys.path[:] = [p for p in sys.path
                   if Path(p or ".").resolve() != _REPO_ROOT.resolve()]
    yield
    sys.path[:] = saved_path
    for k in [k for k in sys.modules if k.startswith(PKG)]:
        del sys.modules[k]
    sys.modules.update(saved_mods)


def _run_header(config):
    """
    Exec the Snakefile header; return its stderr.

    Runs with cwd set to the snakefiles dir because the header reads
    `cluster_config.yaml` by relative path, exactly as it does in a deployed
    recording folder.
    """
    _stub_snakemake()
    err = io.StringIO()
    with contextlib.chdir(_SNAKEDIR), contextlib.redirect_stderr(err):
        exec(compile(_snakefile_header(), "Snakefile", "exec"),
             {"config": dict(config), "__name__": "sf"})
    return err.getvalue()


def _base_config():
    cfg = yaml.safe_load(_CONFIG.read_text())
    cfg["centerline_repo_path"] = str(_REPO_ROOT)
    return cfg


def test_clone_wins_over_installed_copy(tmp_path, clean_imports):
    """The plain case: an installed copy is on sys.path, the clone must win."""
    sys.path.insert(0, str(_fake_installed_package(tmp_path)))
    _run_header(_base_config())
    import centerline_behavior_annotation as pkg
    assert Path(pkg.__file__).is_relative_to(_REPO_ROOT)


def test_clone_wins_even_if_shared_copy_already_imported(tmp_path, clean_imports):
    """
    The hard case. sys.path only governs imports that HAVE NOT HAPPENED YET, so
    if anything imported the shared copy first (a .pth, sitecustomize, a plugin)
    it sits in sys.modules and a path change alone is a no-op. The Snakefile
    must evict it.
    """
    sys.path.insert(0, str(_fake_installed_package(tmp_path)))
    import centerline_behavior_annotation as before  # simulate the early import
    assert not Path(before.__file__).is_relative_to(_REPO_ROOT)

    err = _run_header(_base_config())

    import centerline_behavior_annotation as after
    assert Path(after.__file__).is_relative_to(_REPO_ROOT), (
        "a pre-imported shared copy shadowed the clone")
    assert "evicted" in err


def test_resolved_location_is_always_reported(clean_imports):
    """'Which code actually ran?' must never require detective work."""
    err = _run_header(_base_config())
    assert f"[repo] {PKG} ->" in err


def test_empty_repo_path_warns(clean_imports):
    """Silence here is how the original bug survived; an empty key must shout."""
    cfg = _base_config()
    cfg["centerline_repo_path"] = ""
    err = _run_header(cfg)
    assert "WARNING" in err and "centerline_repo_path" in err


def test_wrong_repo_path_falls_back_to_installed_copy(tmp_path, clean_imports):
    """
    Misconfigured path, but the env does have the package: warn, use it, and say
    plainly that what ran is NOT the configured clone.
    """
    sys.path.insert(0, str(_fake_installed_package(tmp_path)))
    cfg = _base_config()
    cfg["centerline_repo_path"] = str(tmp_path / "does_not_exist")
    err = _run_header(cfg)
    assert "does not contain" in err
    assert f"[repo] {PKG} ->" in err          # reports what it fell back to
    assert "resolved OUTSIDE your configured clone" in err


def test_wrong_repo_path_with_nothing_installed_reports_a_clear_error(
        tmp_path, clean_imports):
    """
    Misconfigured path and nothing installed: the run cannot work, so say so in
    terms that name the fix, rather than letting the first rule die on an
    ImportError deep inside a cluster job.
    """
    cfg = _base_config()
    cfg["centerline_repo_path"] = str(tmp_path / "does_not_exist")
    err = _run_header(cfg)
    assert "ERROR cannot import" in err
    assert "centerline_repo_path" in err


def test_shipped_config_template_has_the_key():
    """
    The deployment scripts stamp this key by regex. If the template ever loses
    it, stamping still works (it prepends), but the documented default and its
    explanatory comment would be gone -- so pin its presence.
    """
    cfg = yaml.safe_load(_CONFIG.read_text())
    assert "centerline_repo_path" in cfg
