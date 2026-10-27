# Development

The user guide is README.md. This file holds build and verification commands for maintainers.

`node_zip_ties/` is the extension source. `tools/package.py` reads its manifest version and builds the ZIP in `dist/`, excluding Python caches. No third-party runtime dependencies are required.

Run the pure geometry checks with:

```text
python -m unittest discover -s tests -v
```

Run each Blender integration script with the installed Blender executable:

```text
blender --background --factory-startup --python-exit-code 1 --python tests/reroute_backend.py
blender --background --factory-startup --python-exit-code 1 --python tests/stable_route_order.py
blender --background --factory-startup --python-exit-code 1 --python tests/evaluation.py
blender --background --factory-startup --python-exit-code 1 --python tests/operators.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/clipboard_reroutes.py
blender --background --factory-startup --python-exit-code 1 --python tests/reroute_undo.py
blender --background --factory-startup --python-exit-code 1 --python tests/rotation_modal.py
blender --background --factory-startup --python-exit-code 1 --python tests/sidebar_ui.py
blender --background --factory-startup --python-exit-code 1 --python tests/move_modal.py
blender --background --factory-startup --python-exit-code 1 --python tests/scale_modal.py
```

Build with `python tools/package.py`. Validate the resulting ZIP with `blender --command extension validate <archive-path>`.

Packaging also updates the current-release download link at the top of both READMEs using the manifest version. Keep this link in future user-guide edits; its HTML comment markers identify the auto-updated block.

`tools/gui_demo.py` prepares an example graph in a graphical session. `tools/preview_tie.py` exports the strap drawing geometry as SVG; this is not an editor screenshot. Rendering the PNG preview requires an optional development rasterizer, not an add-on dependency.

See TESTING.md for test coverage and remaining graphical verification, FEASIBILITY.md for architecture, and PARITY.md for differences from the ComfyUI reference. Preserve LICENSE and THIRD_PARTY_NOTICES.txt when redistributing.
