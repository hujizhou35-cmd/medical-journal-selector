# Contributing

Help make journal selection easier to use and easier to check. We welcome documentation fixes, host compatibility reports, better source checks and evidence-backed improvements to recommendation rules.

## Report a problem or suggest an improvement

[Open an issue](https://github.com/hujizhou35-cmd/medical-journal-selector/issues/new/choose). Include a small reproducible example, your host and version, what you expected and what actually happened. For journal-policy claims, include the source URL and access date. Use fictional or shareable material; do not post unpublished manuscripts, patient data, credentials or restricted databases.

## Submit a pull request

1. Fork the repository and create a branch for one focused change.
2. Edit the canonical source under `skills/`, or the relevant documentation. Keep English and Chinese user-facing pages consistent.
3. Run the relevant checks in the [development guide](../development/README.md). For rule changes, explain the evidence and run affected behavior checks; for a new host claim, report an actual loading test.
4. [Open a pull request](https://github.com/hujizhou35-cmd/medical-journal-selector/compare) describing the problem, change and checks performed.

Generated downloads belong in Releases, not in the source tree. Keep experimental results and original failures intact. A passing software test alone does not establish recommendation accuracy.
