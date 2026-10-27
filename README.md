# Node Zip Ties 0.4.2

A standard Blender 5.2 extension that gathers independent node links into movable cable-tie bundles. Blender draws the wires through managed native reroutes; the add-on draws the strap and locking head. No external dependencies or modified Blender are required.

## Install or update

Install `dist/node_zip_ties-0.4.2.zip` through Edit → Preferences → Get Extensions → menu → Install from Disk. Enable the extension and restart Blender when replacing an already imported version. Open a Geometry, Shader, or Compositor node editor. Existing saved ties are upgraded automatically.

## Controls

| Action | Control |
|---|---|
| Create a tie | Hold Z and drag across at least two wires |
| Move | Drag the strap |
| Select multiple | Ctrl-click toggles; Shift-click adds |
| Rotate freely | R, then mouse movement; click/Enter confirms, Esc/right-click cancels |
| Rotate with snapping | Shift-drag; add Alt for free rotation |
| Color / fixed rotation / removal | Right-click the strap |
| Remove selected ties only | X |
| Remove selected ties and nodes | Delete / Backspace |
| Remove one tie | Double-click or cut across its strap with Z-drag |

The N sidebar contains selected-tie Color/Remove controls, Appearance — All Ties, and Maintenance. Appearance settings affect all trees: Show Straps changes visibility only, spacing and width update the native routes, and New Tie Color affects future ties. The sidebar contains no Tie Wires button, rotation buttons, or Nodes & Ties section.

Optional commands remain available through F3: Box Select Ties and Nodes, Move Selected Nodes and Ties, Copy Nodes with Ties, and Paste Nodes with Ties. These wrappers preserve associated tie metadata. They are not shown in the N sidebar. Ordinary Blender movement and clipboard commands do not fully synchronize straps.

## Persistence and limitations

Each strand uses three reroutes per tie. Their small native handles can remain visible. Existing user-created reroutes are preserved. Removing the last tie restores the direct connection if its route is intact. Broken paths are not silently reconnected; manually rewired helpers can remain as ordinary reroutes.

Routing and tie metadata save with the .blend. Wires continue to evaluate without the add-on. Stable native chain order prevents tie movement from unexpectedly reordering individual strands. Compatibility migrations preserve earlier saved ties and correct older alignment offsets.

Socket positions for gesture picking are estimated for complex node UI layouts. No whole-wire highlight overlay is drawn. Native curves differ from ComfyUI's curves. Graphical event dispatch and visual polish still require manual checks; automated tests cover native graph operations and evaluation.

## Development

`node_zip_ties/` contains the installable source. `tools/package.py` packages the manifest version, excluding Python caches. `tools/gui_demo.py` prepares a native-reroute example in an allowed graphical Blender session.

```text
python -m unittest discover -s tests -v
blender --background --factory-startup --python-exit-code 1 --python tests/reroute_backend.py
blender --background --factory-startup --python-exit-code 1 --python tests/stable_route_order.py
blender --background --factory-startup --python-exit-code 1 --python tests/evaluation.py
blender --background --factory-startup --python-exit-code 1 --python tests/operators.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/clipboard_reroutes.py
blender --background --factory-startup --python-exit-code 1 --python tests/reroute_undo.py
blender --background --factory-startup --python-exit-code 1 --python tests/rotation_modal.py
blender --background --factory-startup --python-exit-code 1 --python tests/sidebar_ui.py
python tools/package.py
blender --command extension validate dist/node_zip_ties-0.4.2.zip
```

See [verification](docs/TESTING.md), [feature checklist](docs/PARITY.md), [architecture](docs/FEASIBILITY.md), and [cleanup audit](docs/CLEANUP.md).

Reference: [ComfyUI Zip Ties](https://github.com/safzanpirani/comfyui-zip-ties), commit `dd31e8d2e3abf5d0f88f44c70723cc52401fd87a`. Original MIT notice is preserved in THIRD_PARTY_NOTICES.txt. [Node Orthogonalizer](https://github.com/Andy294753951/node-orthogonalizer-blender) was inspected as a native-reroute reference; its source is not bundled or imported. Extension license: GPL-3.0-or-later.

G moves the selected ties freely. Press G again (G, G) to slide along a frozen guide of the existing noodle bundle, bounded by neighbouring ties or connected sockets. Sliding does not pass neighbouring ties. Click/Enter confirms; Esc/right-click cancels. Existing click-and-drag movement remains available. Guides average the member noodles and retain the tie angle.

S scales selected ties: strap length and noodle spacing change proportionally around each tie centre, while width and angle stay fixed. Mouse movement sets the factor, or type a number (S, 2, Enter doubles; S, .5, Enter halves). Click/Enter confirms; Esc/right-click cancels. Scale is per tie, persists in the .blend and copies with ties. Existing ties default to scale 1.

Version 0.4.2 restyles the strap with a rounded folded tip, wider locking collar, dark outlines, and body/fold shading. The same geometry drives picking, cuts and box selection. Routing and transform controls are unchanged. A geometry preview is available in docs/tie-style-preview.svg and .png; this is not an editor screenshot.
