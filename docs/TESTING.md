# Verification

Automated checks use stock Blender 5.2.0 LTS on 2026-10-27. This cleanup removes tests of the abandoned overlay curve router and native-patch limitations, while retaining tests for the actual reroute implementation.

| Test | Scope |
|---|---|
| test_geometry.py | Four unit tests: lanes/tangents, cubic intersections, marker hits/cuts and segment endpoints |
| reroute_backend.py | Native routes, no bypass links, helper reuse, multiple ties, removal, muted links, multi-input order, migration, strap alignment, Shader/Compositor and reload |
| stable_route_order.py | Upward/horizontal movement without edge replacement, insertion into existing spans, persistent route order |
| evaluation.py | Identical evaluated cube vertices and polygon indices after real native reroute changes and disable |
| operators.py | Color, fixed rotation, X-only tie removal, no-selection pass-through, mixed native-node/tie removal |
| blender_integration.py | Identity, rename, frame parenting, reconnect, prune, malformed data, reload and registration cleanup |
| clipboard_reroutes.py | Independent pasted tie/endpoint IDs and preserved native helper chains |
| reroute_undo.py | Actual Blender global undo creation/movement and redo |
| scale_modal.py | S mouse/numeric scaling, proportional native gaps and strap length, unchanged width/centre/angle, selection isolation, rollback, helper reuse and save/reload |
| move_modal.py | G free movement, GG frozen curved guides, neighbour bounds, confirm/cancel, key-repeat rejection, click-drag regression and no rewiring |
| rotation_modal.py | Free R rotation, confirm/cancel, angle wrapping, helper reuse and key registration |
| sidebar_ui.py | No sidebar rotation or Nodes & Ties section, R/context rotation retained, selection availability, color initialization and visibility behavior |

Machine-readable results are in tests/*-results.json. UI-contract tests record layout commands; modal tests mock mouse coordinates/registration while updating real Blender graphs. They do not establish rendered layout or real keyboard/mouse dispatch. Graphical verification remains pending because Computer Use previously denied Blender access.

Save tests may emit denied thumbnail-cache writes; .blend save/reload assertions still succeed. Clipboard tests use a workspace temporary directory to avoid the sandbox's default temp restriction. They do not save user preferences.

Manual checks: update/restart Blender; Z-drag several different socket types; move/rotate through neighbouring ties; X-delete, undo/redo, save/reopen; inspect sidebar Color/Remove, Appearance and Maintenance; verify there is no Nodes & Ties section or sidebar rotation/creation button; test socket picking at multiple zoom/DPI levels, frames, nested groups, and complex node layouts.

## G / GG movement — 0.4.0

The keyboard movement operator freezes sampled native noodle spans on invocation. GG projects motion onto an average bundle guide, stopping short of the immediately neighbouring ties/end sockets with clearance for helper points. It does not reorder ties or recreate links. Tie orientation is retained. Missing paths produce a stationary guide. The modal regression test uses real Blender reroutes with mocked mouse coordinates and modal registration. Real UI key dispatch is not verified.

## S scaling — 0.4.1

Scale is an optional validated per-tie multiplier (default 1). Geometry uses it consistently for lane offsets, strap length, marker hits and cuts. Native reroutes reuse the scaled lane positions. Tests confirm mouse doubling, numeric halving, cancellation, centre-start handling, unselected tie preservation, no link/node replacement, and reload. Evaluation remains unchanged after scaling; clipboard tests preserve the scale in pasted ties. Actual editor event dispatch and appearance still need graphical verification.

## Strap style — 0.4.2

The GPU renderer uses convex fan triangulation for the rounded tip and smooth per-vertex colors for gradient shading. The marker outline is shared with hit/cut tests. Five pure geometry tests pass, including rounded-corner exclusion and folded-head picking/cutting. Scale regression passes with the new silhouette. tools/preview_tie.py exports the exact drawing geometry to SVG with GPU calls replaced by vector recording; the PNG preview was rasterized from it and visually inspected. This verifies shape/shading intent, not actual Blender GPU/editor rendering.
