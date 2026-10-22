# Publishing setup

The history/workspace migration supplies independently versioned vosfs and
fss-cli libraries, their historical release tags/assets, CI, and documentation.

The dependent publishing PR adds release-please and PyPI Trusted Publishing.
This foundation intentionally has no active package publishing workflow.
Repository variables `RELEASE_ENABLED` and `PYPI_ENABLED` remain false until
that PR is reviewed, merged, and the PyPI/TestPyPI publishers are configured.

Historical release tags and assets must remain unchanged. See the
[migration record](migration/README.md) for their provenance.
