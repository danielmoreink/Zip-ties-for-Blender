"""Managed native reroutes. Blender draws every noodle; overlays draw only straps.

The user approved reroutes on 2026-10-27. Routing nodes persist and continue to
evaluate in vanilla Blender with this extension disabled.
"""
import json
from . import geometry as g

OWNER = '_nzt_connection'
TIE = '_nzt_tie'
SLOT = '_nzt_slot'
LAYOUT_KEY = '_nzt_layout_version'
LAYOUT_VERSION = 2


def managed(node):
    return node.bl_idname == 'NodeReroute' and bool(node.get(OWNER))


def connection_key(link):
    from . import data
    a = link.from_node.get(OWNER) if managed(link.from_node) else None
    b = link.to_node.get(OWNER) if managed(link.to_node) else None
    if a and b and a != b:
        return data.physical_key(link)
    return a or b or data.physical_key(link)


def endpoints(tree, key):
    from . import data
    try:
        source, output, target, input_ = json.loads(key)
        nodes = {data.uid(n): n for n in tree.nodes if not managed(n)}
        a, b = nodes.get(source), nodes.get(target)
        if not a or not b:
            return None
        out = next((s for s in a.outputs if s.identifier == output), None)
        inp = next((s for s in b.inputs if s.identifier == input_), None)
        return (out, inp) if out and inp else None
    except (ValueError, TypeError):
        return None


def path(tree, key):
    """Only count complete paths through this connection's own managed helpers."""
    pair = endpoints(tree, key)
    if not pair:
        return []
    source, target = pair
    outgoing = {}
    for link in tree.links:
        outgoing.setdefault(link.from_socket.as_pointer(), []).append(link)
    stack = [(source, [])]
    visited = set()
    while stack:
        socket, chain = stack.pop()
        ptr = socket.as_pointer()
        if ptr in visited:
            continue
        visited.add(ptr)
        for link in outgoing.get(ptr, []):
            if link.to_socket == target:
                return chain + [link]
            node = link.to_node
            if managed(node) and node.get(OWNER) == key:
                stack.append((node.outputs[0], chain + [link]))
    return []


def live_keys(tree):
    candidates = {connection_key(l) for l in tree.links}
    return {k for k in candidates if path(tree, k)}


def _center(node, point):
    # Blender 5.2 reroute_node_prepare_for_draw places both socket centres
    # directly at node_to_view(node.location), with bounds around that point.
    # A reroute is not positioned by the top-left corner of its drawing box.
    node.location_absolute = point


def ordered_ties(applicable, old_path, source, target):
    """Keep native chain order fixed during transforms, including after reload.

    Only a newly added tie is inserted, at the nearest existing route span.
    Re-sorting by the source/destination chord on every drag can swap ties at
    different heights, separately for each strand, causing sudden rewiring.
    """
    from .sockets import socket_position
    by_id = {t['id']:t for t in applicable}
    seen = set()
    ordered = []
    for link in old_path:
        identity = link.to_node.get(TIE) if managed(link.to_node) else None
        if identity in by_id and identity not in seen:
            ordered.append(by_id[identity])
            seen.add(identity)

    def distance_squared(p,a,b):
        d = g.sub(b,a)
        length = g.dot(d,d)
        t = max(0,min(1,g.dot(g.sub(p,a),d)/length)) if length else 0
        delta = g.sub(p,g.add(a,g.mul(d,t)))
        return g.dot(delta,delta)

    for tie in applicable:
        if tie['id'] in seen:
            continue
        anchors = [socket_position(source.node,source)] + [t['pos'] for t in ordered] + [socket_position(target.node,target)]
        index = min(range(len(anchors)-1),
                    key=lambda i:distance_squared(tie['pos'],anchors[i],anchors[i+1]))
        ordered.insert(index,tie)
        seen.add(tie['id'])
    return ordered


def sync(tree, ties, spacing=4.5, width=5):
    """Reconcile routes in the caller's undo step. Moving ties reuses all nodes.

    Broken paths are never resurrected. Helpers that a user manually rewired
    remain ordinary reroutes rather than destroying those edits.
    """
    by_key = {}
    for tie in ties:
        for key in tie['members']:
            by_key.setdefault(key, []).append(tie)
    helpers = {}
    for node in tree.nodes:
        if managed(node):
            helpers.setdefault(node[OWNER], []).append(node)
    for key in set(by_key) | set(helpers):
        old_nodes = helpers.get(key, [])
        old_path = path(tree, key)
        if not old_path:
            # A user cut/deleted/reconnected this path. Retain any remaining
            # helpers as normal reroutes; do not invent a new connection.
            for node in old_nodes:
                for attr in (OWNER,TIE,SLOT):
                    if attr in node:
                        del node[attr]
            continue
        source, target = endpoints(tree, key)
        applicable = by_key.get(key, [])
        applicable = ordered_ties(applicable,old_path,source,target)
        existing = {(n.get(TIE), n.get(SLOT)): n for n in old_nodes}
        desired_nodes = []
        # Three points keep each strand parallel through the strap and make
        # rotation effective using Blender's reroute tangent calculation.
        for tie in applicable:
            centre, tangent = g.lane(tie, key, spacing)
            for slot, distance in enumerate((-max(12,width), 0, max(12,width))):
                identity = (tie['id'], slot)
                node = existing.get(identity)
                if node is None:
                    node = tree.nodes.new('NodeReroute')
                    node[OWNER], node[TIE], node[SLOT] = key, tie['id'], slot
                    node.select = False
                    from .data import uid
                    uid(node, True)
                _center(node, g.add(centre, g.mul(tangent, distance)))
                desired_nodes.append(node)
        edges = {(l.from_socket.as_pointer(),l.to_socket.as_pointer()):l for l in old_path}
        old_terminal = old_path[-1]
        mute = any(l.is_muted for l in old_path)
        kept = set()
        for index in range(len(desired_nodes)+1):
            # A reroute's sockets can be rebuilt when Blender infers its type
            # from the preceding link. Never retain those socket RNA objects
            # across tree.links.new calls.
            out = source if index == 0 else desired_nodes[index-1].outputs[0]
            inp = target if index == len(desired_nodes) else desired_nodes[index].inputs[0]
            edge = (out.as_pointer(),inp.as_pointer())
            link = edges.get(edge)
            if link is None:
                # Do not let single-input auto-replacement invalidate references
                # to old_path while we are constructing the new chain.
                link = tree.links.new(out,inp,verify_limits=False)
                if link is None:
                    raise RuntimeError('Blender could not connect a zip-tie reroute')
                if inp == target and target.is_multi_input:
                    link.swap_multi_input_sort_id(old_terminal)
                link.is_muted = mute
            kept.add(link.as_pointer())
        live = {l.as_pointer(): l for l in tree.links}
        for link in old_path:
            ptr = link.as_pointer()
            if ptr not in kept and ptr in live:
                tree.links.remove(link)
        wanted = {n.as_pointer() for n in desired_nodes}
        for node in old_nodes:
            if node.as_pointer() not in wanted:
                # Preserve unexpected user branches attached to a helper.
                if any(l.from_node == node or l.to_node == node for l in tree.links):
                    for attr in (OWNER,TIE,SLOT):
                        if attr in node:
                            del node[attr]
                else:
                    tree.nodes.remove(node)
    tree[LAYOUT_KEY] = LAYOUT_VERSION


def settings():
    import bpy
    from .preferences import prefs
    options = prefs(bpy.context)
    return options.spacing, options.width
