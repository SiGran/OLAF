Contributing
============

This page explains how the OLAF development workflow works — what happens
when code is pushed to GitHub, how the automated checks keep the codebase
healthy, and how you can contribute even if you are not a software engineer.

The full step-by-step guide (including how to fix failing checks) lives in
`CONTRIBUTING.md <https://github.com/SiGran/OLAF/blob/develop/CONTRIBUTING.md>`_
in the repository root. The sections below give a high-level overview.

----

Setting up
----------

All dependencies — including the development tools — are managed by
`uv <https://docs.astral.sh/uv/>`_. After cloning the repository, one
command installs everything:

.. code-block:: bash

   uv sync --all-extras

----

The CI pipeline
---------------

Every pull request triggers five automated checks that run in parallel on
GitHub Actions. All five must pass before a PR can be merged.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Job name
     - Tool
     - What it checks
   * - ``lint``
     - ruff
     - Code style and formatting (import order, unused variables, line length, …)
   * - ``typecheck``
     - mypy
     - Type annotations are consistent — catches bugs like a function that
       claims to return ``float`` but can silently return ``None``
   * - ``security``
     - bandit
     - Common security issues (hardcoded secrets, unsafe temp files, …)
   * - ``pre-commit``
     - pre-commit hooks
     - File hygiene: trailing whitespace, missing newlines, valid YAML/TOML,
       no leftover merge-conflict markers
   * - ``test``
     - pytest
     - Full test suite on Python 3.11 *and* 3.12; GUI tests are skipped
       automatically on headless runners

A final ``ci-success`` job aggregates all five results into a single status
check. Branch protection requires only this one check, so you always get a
clear green ✓ or red ✗ on every PR.

----

Running checks locally
----------------------

You can run the exact same checks on your machine before pushing:

.. code-block:: bash

   uv run ruff check --fix .          # auto-fix style issues
   uv run mypy .                       # type checking
   uv run bandit -r olaf               # security scan
   uv run pre-commit run --all-files   # file hygiene
   uv run pytest -m "not gui"          # test suite

----

Test coverage
-------------

Test results are uploaded to `Codecov <https://codecov.io/gh/SiGran/OLAF>`_,
which posts a summary on every pull request. To generate a local coverage
report:

.. code-block:: bash

   uv run pytest -m "not gui" --cov=olaf --cov-report=term

----

Further reading
---------------

See `CONTRIBUTING.md <https://github.com/SiGran/OLAF/blob/develop/CONTRIBUTING.md>`_
for the full guide, including what to do when each check fails.
