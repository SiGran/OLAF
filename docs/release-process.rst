Release Process
===============

This page describes how to promote a release from ``develop`` to ``main``.

Step-by-step
------------

1. **Bump the version** in ``pyproject.toml``::

       version = "X.Y.Z"

   Follow `Semantic Versioning <https://semver.org/>`_:
   MAJOR for breaking changes, MINOR for new features, PATCH for bug fixes.

2. **Update release notes** (if a CHANGELOG is maintained).

3. **Open a PR from** ``develop`` **to** ``main``.

4. The **Release gate** workflow runs automatically and verifies:

   - Full Python matrix (3.11, 3.12, 3.13) is green.
   - Non-GUI test suite passes.
   - Docs build cleanly with ``-W`` (warnings treated as errors).
   - ``pyproject.toml`` version was bumped vs ``main`` — the job fails if you
     forgot this step.

5. **Merge** the PR after all release-gate checks are green.

6. **Tag the release**::

       git tag vX.Y.Z
       git push --tags

7. Docs are **auto-deployed** to GitHub Pages on push to ``main`` via the
   Documentation workflow.

Release gate status check
-------------------------

On the ``main`` branch protection rule, require the ``Release gate success``
status check (the ``release-gate-success`` job). This is separate from the
``CI success`` check used on ``develop`` PRs.

Adding integration tests
------------------------

Currently the release gate runs the full non-GUI suite as a proxy for
integration tests. Once real-data integration tests are tagged with
``@pytest.mark.integration``, update ``release-gate.yml`` to use::

    uv run pytest -m "integration and not gui" -v

and remove the comment noting the workaround.
