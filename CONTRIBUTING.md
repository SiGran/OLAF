# Contributing to OLAF

Thank you for your interest in contributing to OLAF! This guide is written for scientists
and researchers who may not be deeply familiar with software development practices. It
explains how to get your changes into the codebase, what the automated checks do, and how
to fix things when they go wrong.

---

## Table of contents

1. [Setting up your development environment](#1-setting-up-your-development-environment)
2. [Making a change](#2-making-a-change)
3. [Running checks locally before pushing](#3-running-checks-locally-before-pushing)
4. [What the automated CI checks do](#4-what-the-automated-ci-checks-do)
5. [What to do when a check fails](#5-what-to-do-when-a-check-fails)
6. [Understanding test coverage](#6-understanding-test-coverage)
7. [Opening a pull request](#7-opening-a-pull-request)

---

## 1. Setting up your development environment

Follow the installation instructions in the [README](README.md) to install `uv` and Python.

Once `uv` is installed, clone the repository and install all dependencies (including
development tools) with one command:

```bash
git clone https://github.com/SiGran/OLAF.git
cd OLAF
uv sync --all-extras
```

This creates a virtual environment and installs everything needed to run the code *and*
the quality checks.

---

## 2. Making a change

1. Create a new branch from `develop` for your work:
   ```bash
   git checkout develop
   git pull
   git checkout -b my-descriptive-branch-name
   ```
2. Make your changes to the code.
3. Run the checks locally (see next section) before pushing.
4. Commit and push your branch, then open a Pull Request against `develop` on GitHub.

---

## 3. Running checks locally before pushing

These are the exact same commands that run automatically on GitHub. Running them
locally first saves you time — you get feedback in seconds instead of waiting for
the cloud to finish.

```bash
# Auto-fix simple style issues (import order, whitespace, etc.)
uv run ruff check --fix .

# Check for any remaining style / logic issues
uv run ruff check .

# Check that type annotations are consistent
uv run mypy .

# Scan for common security issues
uv run bandit -r olaf

# Run all pre-commit hooks (same hooks that run on every commit in CI)
uv run pre-commit run --all-files

# Run the test suite (skips GUI tests that need a screen)
uv run pytest -m "not gui"
```

You can also run the pre-commit hooks automatically every time you commit by
installing them once:

```bash
uv run pre-commit install
```

After that, the hooks run silently whenever you `git commit`.

---

## 4. What the automated CI checks do

Every time you push code or open a pull request, GitHub automatically runs five
checks in parallel. Here is what each one does in plain language:

### `lint` — code style (ruff)
Checks that the code follows consistent formatting and style rules — things like
import order, unused variables, and line length. This isn't about being picky; it
makes the code easier to read and review for everyone.

> **Why it matters for scientists:** consistent style means you can focus on the
> *science* in the code rather than deciphering formatting quirks.

### `typecheck` — type consistency (mypy)
Verifies that functions receive and return the types they claim to. For example,
if a function says it returns a `float` but actually returns `None` in some branch,
mypy will catch that before it becomes a runtime error mid-analysis.

### `security` — vulnerability scan (bandit)
Scans for common security problems such as hardcoded passwords or unsafe use of
temporary files. Low noise — only flags things that actually matter.

### `pre-commit` — file hygiene hooks
Runs a set of lightweight checks on every file:
- No trailing whitespace
- Files end with a newline
- YAML and TOML configuration files are valid
- No unresolved merge conflict markers (`<<<<<<<`) accidentally left in

### `test` — automated tests (pytest)
Runs the test suite on Python 3.11 **and** 3.12 to make sure the code works on
both versions. Tests skip anything that needs a display (GUI tests) so they run
cleanly in the cloud.

---

### The `CI success` gate

All five checks must pass before a pull request can be merged. Rather than requiring
each check individually, the branch protection rule only requires one combined status
called **"CI success"** — this passes automatically once all five jobs finish green.
If any job fails you will see a red ✗ on the PR; click it to see which job failed
and why.

---

## 5. What to do when a check fails

### `lint` failed
```bash
# Let ruff fix what it can automatically
uv run ruff check --fix .
# Then check if anything needs manual attention
uv run ruff check .
```
The output tells you the file, line number, and a short code (e.g. `F401` = unused
import, `E501` = line too long). Click the code in the GitHub UI to see the full
explanation.

### `typecheck` failed
```bash
uv run mypy .
```
Mypy prints the file, line, and a description like
`Incompatible return value type (got "None", expected "float")`.
Fix the code or, for cases where you are certain mypy is wrong, add a
`# type: ignore  # <short reason>` comment on that line.

### `security` failed
```bash
uv run bandit -r olaf
```
Bandit prints the file, line, severity, and a CWE reference. Low-severity findings
can usually be suppressed with `# nosec` if they are false positives; medium/high
findings should be fixed.

### `pre-commit` failed
```bash
uv run pre-commit run --all-files
```
Pre-commit auto-fixes most issues (trailing whitespace, missing newlines). Re-run
`git add` on the fixed files and commit again.

### `test` failed
```bash
uv run pytest -m "not gui" -v
```
The `-v` flag shows which specific tests failed. Each test failure prints what
value was expected versus what was actually produced.

---

## 6. Understanding test coverage

After the test job runs, coverage results are uploaded to
[Codecov](https://codecov.io/gh/SiGran/OLAF). Codecov posts a summary comment on
pull requests showing which lines of code are exercised by the tests and which are not.

A **coverage percentage** near 100% means almost every line is tested; a low percentage
means some code paths are untested and could contain hidden bugs. You don't need to
achieve 100% — but if you add new processing logic, adding a test for it is strongly
encouraged.

To generate a coverage report locally:
```bash
uv run pytest -m "not gui" --cov=olaf --cov-report=term
```

---

## 7. Opening a pull request

1. Push your branch to GitHub:
   ```bash
   git push -u origin my-descriptive-branch-name
   ```
2. GitHub will show a banner prompting you to **"Compare & pull request"** — click it.
3. Set the base branch to `develop`.
4. Write a short description of *what* you changed and *why*.
5. The CI checks will start automatically. You can watch them at the bottom of the PR page.
6. Once all checks are green and someone has reviewed the PR, it can be merged.

---

## Questions?

If you are unsure about anything, open a
[GitHub Discussion](https://github.com/SiGran/OLAF/discussions) or
[issue](https://github.com/SiGran/OLAF/issues) — there are no silly questions.
