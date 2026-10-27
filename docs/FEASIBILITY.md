# Current architecture â€” 0.2.0

The user approved native reroutes to prioritize the aesthetic outcome. This is a standard Blender add-on.

`routing.py` replaces each logical direct link with a chain of native NodeReroute nodes: three points per tie per strand, in stable native chain order; newly created ties insert into the nearest route span. Lane offset fixes strand order; entry, centre and exit positions follow tie rotation. Blender retains responsibility for drawing native links, colors and field dashes. The overlay draws straps and gesture indicators only, never alternate noodles.

Each helper stores its original connection key, tie UUID and role. Original endpoints use node UUIDs plus socket identifiers. `data.write` reconciles native routes inside the calling operator's undo step, reusing nodes and links during motion. Single-input links are constructed without automatic limit replacement; obsolete owned edges are then removed. Multi-input sort IDs are swapped onto replacement terminal links before old terminal links are removed. Muted state is preserved. Reroute sockets are fetched anew after every connection because Blender can rebuild them when inferring their type.

When a tie is removed, intact chains reconnect through the remaining ties, or directly when no tie remains. Broken chains are not reconnected. Unexpected user branches and remaining broken helpers are retained as ordinary reroutes rather than destroyed. Existing user reroutes are independent endpoints. These cases may leave harmless routing nodes that the user can remove manually.

Runtime handlers never modify graph data during drawing. A one-shot registration migration and load handler convert old overlay-only ties. JSON metadata plus native nodes participate in save/reload and Blender undo. Native helpers continue functioning without the extension. Clipboard wrappers copy the relevant helpers and remap endpoint IDs, tie IDs and helper ownership on paste.

The former Python API findings still apply: native link paths and socket runtime positions are not exposed as writable public RNA. We no longer need a link rendering override because actual links now run through reroutes. Gesture hit-testing still estimates socket locations, so custom UI layouts and collapsed nodes need more visual testing. Native reroute tangents/handles determine curve shape; this is not an exact recreation of LiteGraph's cubic controls.


Optional per-tie scale multiplies the lane spacing and strap half-length (including padding), preserving the tie centre, angle and width. Old data with no scale uses 1. The S modal stores this multiplier with the tie JSON; no schema-version change or graph-evaluation node is required.
