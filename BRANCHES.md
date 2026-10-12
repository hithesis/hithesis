# Branch roles

- `master`: released hithesis, retaining the existing document interfaces.
- `dev`: maintenance and reviewed improvements based directly on master; merge
  ready changes into master through pull requests.
- `docxlike`: modular Word-style layout and v4 interface development. This branch
  incorporates the former local dev, modularity and Andrew's-test histories.

The v3.2a release preserves `hithesisbook`, `hithesisart` and `hithesisartplus`.
Removal belongs to v4, tentatively around early 2027. The docxlike branch is a v4
development preview, not the published v3.2a implementation.

The common LaTeX minimum is 2023-06-01. wiseref remains independently distributed;
standalone example bundles carry its unmodified runtime and license only.

The development snapshot before master integration is commit `29e877b`.
The former Andrew's-test tip `a55d4c5`, old upstream dev `50357f1` and modularity
tip `5c700d7` are retained in the docxlike history before retiring their old names.
