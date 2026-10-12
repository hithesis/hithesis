# Branch roles

- `master`: published releases.
- `dev`: maintenance development based on master, retaining the three original
  document classes and their public syntax; reviewed changes merge through PRs.
- `docxlike`: modular Word-style layout and v4 interface development, preserving
  the former dev, modularity and Andrew's-test histories.

The published v3.2a release keeps the original class names. Their removal belongs
to v4, tentatively around early 2027. The docxlike branch is a v4 development
preview and is not the v3.2a implementation.

Both development lines use a LaTeX 2023-06-01 minimum and the independently
distributed wiseref package. User bundles include its runtime and license only.
