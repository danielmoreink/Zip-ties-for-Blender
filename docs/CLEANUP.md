# Cleanup audit — 0.3.4

Removed:

- Native-patch detection and exact-coordinate branch in sockets.py.
- Unused custom cubic routing algorithm, including its obsolete chord-sorting tests. Curve sampling/intersection code stays because gesture picking still uses it.
- Unused smoothness default and an always-true rendering availability gate, including its unreachable warnings.
- Duplicate generic COLOR action/dialog; the dedicated color operator is now the single path.
- Unused gesture snapshot, highlight-preview keys, imports, and obsolete documentation/release appendices.
- Entire native patch/source-download directory; patch generator/checker; two one-off API/socket probes; API-limitation-only test and result.
- Nodes & Ties sidebar panel and registration. Its functioning optional operators remain available through F3.

Retained deliberately:

- Saved-data and layout migrations. These are compatibility code for existing user .blend files, not abandoned runtime paths.
- R and Shift-drag rotation; context-menu fixed-angle commands.
- Native reroute routing, hit-testing geometry, clipboard mapping, selection, undo and active regression tests.
- Original MIT notices and reference attribution.

Existing older release ZIPs and ignored reference/research checkouts are not part of the runtime package and were left untouched. Only the current manifest version is rebuilt.
