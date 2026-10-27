# Current feature checklist â€” 0.2.0

The user approved reroutes to prioritize appearance. Stock Blender draws the actual routed connections; no alternate noodle overlays are drawn.

| Feature | Current status |
|---|---|
| Native bundled wires without duplicate originals | Implemented; automated tests prove no direct bypass links remain. |
| G / GG / click-drag | G free movement, second G bounded sliding along the existing bundle, click-drag retained; modal contracts tested. |
| Move/rotate tie, stable lanes, multiple ties | Implemented; native helper positions, reuse, lane order and chain counts tested. |
| Z-drag / menu creation / cutting markers | Implemented; gesture UI verification pending. |
| Ctrl/Shift selection, context menu, double-click | Implemented; UI verification pending. |
| 15-degree snapping and Alt free rotation | Implemented; native routing follows stored angle. |
| Random/grey/wire-matched colors, strap/head, hover border | Implemented; native reroute handles remain visible near straps. |
| White whole-wire gesture/hover highlight | Removed: drawing approximate overlays could resemble duplicated wires. Gesture line and marker cut highlighting remain. |
| Independent data types / existing reroutes | Geometry/vector/float evaluation and user reroute graph tested. |
| Native field dashes and socket colors | Native Blender drawing is used unchanged. Visual confirmation pending. |
| Delete last tie restores direct connections | Tested; managed helpers removed, original endpoint keys restored. |
| Muted links / multi-input order | Tested through tie creation/removal. |
| Broken path / reconnect | Complete-path detection tested; broken paths not resurrected; dangling helpers may remain as ordinary nodes. |
| Rename / frames / nested trees | Stable endpoint identity and frame parenting tested; nested UI navigation pending. |
| Save/reload / disable / uninstall | Native wiring persists and evaluates without extension; tests pass. |
| Upgrade old overlay-only ties | Migration on register/load implemented. |
| Undo/redo | Background Blender global undo creation/movement and redo tested. Gesture-level history pending. |
| Copy/paste | Optional F3 wrapper tested with independent IDs and reused copied helpers. Native Ctrl-C/V does not fully preserve strap metadata. |
| Joint movement / box selection | Optional F3 commands implemented; ordinary native movement/box tools do not yet synchronize all tie behavior. |
| Zoom/DPI/custom node layouts | Native wires remain correct; gesture coordinate estimates and marker sizing require UI validation. |

No claim of exact ComfyUI curve/interaction parity is made. The key improvement is functional native routing in an ordinary add-on, using the newly accepted reroute approach.
