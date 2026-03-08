#!/usr/bin/env python3
"""Run backend and frontend test suites across all downstream apps."""

import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

from workspace import get_repos

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent          # ModernAppTemplate/
WORK = REPO_ROOT.parent                # parent of ModernAppTemplate (e.g. /work)
APPS = ["ElectronicsInventory", "IoTSupport", "DHCPApp", "ZigbeeControl"]
RESULTS_FILE = REPO_ROOT / "test_results.md"

HAS_PYTHON313 = shutil.which("python3.13") is not None


def run(args, cwd, timeout=600):
    """Run a command, return (success, stdout+stderr)."""
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        combined = result.stdout + result.stderr
        return result.returncode == 0, combined
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s: {' '.join(str(a) for a in args)}"


COLS = 80
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"

USE_COLOR = sys.stderr.isatty()


def _c(code, text):
    return f"{code}{text}{RESET}" if USE_COLOR else text


def progress_start(msg):
    """Print ' * Starting foo...' without newline (SysV init style)."""
    line = f" * {msg}..."
    print(line, end="", file=sys.stderr, flush=True)
    return len(line)


def progress_end(ok, col_used):
    """Print right-aligned [ OK ] or [FAIL] to finish the line."""
    tag = _c(GREEN, "[ OK ]") if ok else _c(RED, "[FAIL]")
    tag_plain = "[ OK ]" if ok else "[FAIL]"
    padding = max(1, COLS - col_used - len(tag_plain))
    print(" " * padding + tag, file=sys.stderr, flush=True)


def progress_skip(col_used):
    """Print right-aligned [skip] for skipped steps."""
    tag = _c(YELLOW, "[skip]")
    padding = max(1, COLS - col_used - len("[skip]"))
    print(" " * padding + tag, file=sys.stderr, flush=True)


def progress_header(app_name):
    """Print a boot-style header for an app."""
    print(file=sys.stderr)
    print(_c(BOLD, f" --- {app_name} ---"), file=sys.stderr, flush=True)


def run_app(app_name):
    """Run all steps for one app. Returns list of (step, passed, detail)."""
    backend = WORK / app_name / "backend"
    frontend = WORK / app_name / "frontend"
    results = []

    # --- Backend ---
    if backend.is_dir():
        # poetry install
        col = progress_start(f"Installing {app_name} backend dependencies")
        cmds = []
        if HAS_PYTHON313:
            cmds.append(["poetry", "env", "use", "python3.13"])
        cmds.append(["poetry", "install", "--no-interaction"])

        ok = True
        detail = ""
        for cmd in cmds:
            ok, detail = run(cmd, cwd=backend)
            if not ok:
                if "lock" in detail.lower() or "locked" in detail.lower():
                    run(["poetry", "lock", "--no-update", "--no-interaction"], cwd=backend, timeout=300)
                    ok, detail = run(cmd, cwd=backend)
            if not ok:
                break
        progress_end(ok, col)

        results.append(("backend install", ok, detail))
        if not ok:
            col = progress_start(f"Running {app_name} backend tests")
            progress_skip(col)
            results.append(("backend pytest", False, "Skipped (install failed)"))
        else:
            col = progress_start(f"Running {app_name} backend tests")
            ok, detail = run(["poetry", "run", "pytest", "-v", "--tb=short"], cwd=backend, timeout=300)
            progress_end(ok, col)
            results.append(("backend pytest", ok, detail))
    else:
        col = progress_start(f"Installing {app_name} backend dependencies")
        progress_end(False, col)
        results.append(("backend install", False, f"Directory not found: {backend}"))

    # --- Frontend ---
    if frontend.is_dir():
        col = progress_start(f"Installing {app_name} frontend dependencies")
        pnpm_install = ["pnpm", "install", "--frozen-lockfile", "--config.confirmModulesPurge=false"]
        ok, detail = run(pnpm_install, cwd=frontend, timeout=120)
        if not ok:
            ok, detail = run(["pnpm", "install", "--config.confirmModulesPurge=false"], cwd=frontend, timeout=120)
        progress_end(ok, col)
        results.append(("frontend install", ok, detail))

        if not ok:
            for label in ("frontend build", "playwright"):
                col = progress_start(f"{'Building' if 'build' in label else 'Running'} {app_name} {label}")
                progress_skip(col)
                results.append((label, False, "Skipped (install failed)"))
        else:
            col = progress_start(f"Building {app_name} frontend")
            ok, detail = run(["pnpm", "build"], cwd=frontend, timeout=300)
            progress_end(ok, col)
            results.append(("frontend build", ok, detail))

            if not ok:
                col = progress_start(f"Running {app_name} playwright tests")
                progress_skip(col)
                results.append(("playwright", False, "Skipped (build failed)"))
            else:
                col = progress_start(f"Running {app_name} playwright tests")
                ok, detail = run(
                    ["pnpm", "playwright", "test", "--reporter=list"],
                    cwd=frontend, timeout=600,
                )
                progress_end(ok, col)
                results.append(("playwright", ok, detail))
    else:
        col = progress_start(f"Installing {app_name} frontend dependencies")
        progress_end(False, col)
        results.append(("frontend install", False, f"Directory not found: {frontend}"))

    return results


def _extract_pytest_failures(detail):
    """Extract failed test names from pytest output (summary lines only)."""
    failed = []
    for line in detail.splitlines():
        stripped = line.strip()
        # Match only the summary lines: "FAILED tests/path::Class::test_name"
        # Skip verbose progress lines: "tests/path::test FAILED [ 7%]"
        if stripped.startswith("FAILED "):
            failed.append(stripped)
    return failed


def _extract_playwright_failures(detail):
    """Extract failed test names from playwright list reporter output."""
    failed = []
    for line in detail.splitlines():
        stripped = line.strip()
        # Skip artifact paths like "test-results/e2e-...-chromium/test-failed-1.png"
        if "test-results/" in stripped:
            continue
        # Match lines like: "✘  1 [chromium] › e2e/foo.spec.ts:10:5 › describe › test (5s)"
        if "›" in stripped and ("✘" in stripped or "[chromium]" in stripped):
            failed.append(stripped)
            continue
        # Match summary count: "11 failed"
        if stripped.endswith(" failed") and stripped.split()[0].isdigit():
            failed.append(stripped)
    return failed


def format_summary(all_results):
    """Build the terse stdout summary."""
    lines = []
    any_failure = False

    for app_name, steps in all_results:
        failures = [(step, detail) for step, ok, detail in steps if not ok]
        if failures:
            any_failure = True
            lines.append(f"\n{app_name}: FAILURES")
            for step, detail in failures:
                if "Skipped" in detail:
                    lines.append(f"  {step}: {detail}")
                elif step == "backend pytest":
                    extracted = _extract_pytest_failures(detail)
                    for line in extracted:
                        lines.append(f"  {line}")
                    if not extracted:
                        lines.append(f"  {step}: failed (see test_results.md)")
                elif step == "playwright":
                    extracted = _extract_playwright_failures(detail)
                    for line in extracted:
                        lines.append(f"  {line}")
                    if not extracted:
                        lines.append(f"  {step}: failed (see test_results.md)")
                else:
                    lines.append(f"  {step}: FAILED (see test_results.md)")
        else:
            passed = ", ".join(step for step, ok, _ in steps)
            lines.append(f"\n{app_name}: all passed ({passed})")

    if not any_failure:
        lines.append("\nAll apps passed all steps.")

    return "\n".join(lines) + "\n"


def format_app_detailed(app_name, steps):
    """Build the detailed test_results.md section for one app."""
    lines = [f"## {app_name}\n"]
    for step, ok, detail in steps:
        status = "PASS" if ok else "FAIL"
        lines.append(f"### {step}: {status}\n")
        if not ok and detail and "Skipped" not in detail:
            lines.append("```")
            # Trim very long output to last 200 lines
            output_lines = detail.splitlines()
            if len(output_lines) > 200:
                lines.append(f"... ({len(output_lines) - 200} lines trimmed) ...")
                output_lines = output_lines[-200:]
            lines.extend(output_lines)
            lines.append("```\n")
        elif not ok:
            lines.append(f"{detail}\n")

    return "\n".join(lines) + "\n"


def main():
    all_results = []

    # Write header immediately
    RESULTS_FILE.write_text("# Test Results\n\n")

    for app_name in APPS:
        progress_header(app_name)
        steps = run_app(app_name)
        all_results.append((app_name, steps))

        # Append this app's results incrementally
        with RESULTS_FILE.open("a") as f:
            f.write(format_app_detailed(app_name, steps))

    print(f"\nDetailed results written to {RESULTS_FILE}", file=sys.stderr)

    # Return summary for stdout
    print(format_summary(all_results))


if __name__ == "__main__":
    if sys.stdout.isatty():
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        main()
        sys.stdout = old_stdout
        output = buf.getvalue()
        if output:
            pager = subprocess.Popen(
                ["less", "-R"],
                stdin=subprocess.PIPE,
                env={**os.environ, "LESSCHARSET": "utf-8"},
            )
            try:
                pager.communicate(input=output.encode())
            except KeyboardInterrupt:
                pager.kill()
    else:
        main()
