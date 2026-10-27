"""Versioned tie storage, with stable logical connections through managed reroutes."""
import json
import math
import uuid

KEY = '_node_zip_ties_v1'
NODE_ID = '_node_zip_ties_uuid'


def uid(node, create=False):
    value = node.get(NODE_ID, '')
    if not value and create:
        value = uuid.uuid4().hex
        node[NODE_ID] = value
    return value


def physical_key(link, create=False):
    # JSON encoding prevents collisions for custom socket identifiers with punctuation.
    return json.dumps([uid(link.from_node, create), link.from_socket.identifier,
                       uid(link.to_node, create), link.to_socket.identifier], separators=(',', ':'))


def link_key(link, create=False):
    from . import routing
    if create:
        uid(link.from_node, True)
        uid(link.to_node, True)
    return routing.connection_key(link)


def read(tree):
    try:
        raw = json.loads(tree.get(KEY, '{}'))
        if raw.get('version') != 1:
            return []
        result = []
        seen = set()
        for t in raw.get('ties', []):
            if (not isinstance(t, dict) or not isinstance(t.get('id'), str) or t['id'] in seen or
                len(t.get('pos', [])) != 2 or not all(isinstance(v, (int,float)) and math.isfinite(v) for v in t['pos']) or
                not isinstance(t.get('angle'), (float,int)) or not math.isfinite(t['angle']) or
                not isinstance(t.get('members'), list) or not t['members'] or
                not all(isinstance(k, str) for k in t['members'])):
                continue
            color = t.get('color', [.55,.55,.58,1])
            if len(color) != 4 or not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in color):
                continue
            t['color'] = color
            if 'scale' in t:
                value = t['scale']
                t['scale'] = max(.1,min(20,value)) if isinstance(value,(int,float)) and math.isfinite(value) and value>0 else 1.0
            t['members'] = list(dict.fromkeys(t['members']))
            seen.add(t['id'])
            result.append(t)
        return result
    except (ValueError, TypeError, AttributeError):
        return []


def write(tree, ties):
    from . import routing
    spacing,width = routing.settings()
    routing.sync(tree,ties,spacing,width)
    tree[KEY] = json.dumps({'version': 1, 'ties': ties}, separators=(',', ':'), allow_nan=False)


def new_tie(pos, angle, keys, ties, color):
    twin = next((t for t in ties if set(keys) <= set(t['members'])), None)
    if twin:
        keys = sorted(keys, key=twin['members'].index)
    return dict(id=uuid.uuid4().hex, pos=list(pos), angle=angle, members=keys, color=list(color))


def prune(tree, ties):
    from . import routing
    live = routing.live_keys(tree)
    for t in ties:
        t['members'] = [k for k in t['members'] if k in live]
    return [t for t in ties if t['members']]


def repair_duplicate_ids(tree):
    """Run only in explicit edits, never draw callbacks. Preserve original identity."""
    seen = set()
    for n in tree.nodes:
        value = uid(n, True)
        if value in seen:
            n[NODE_ID] = uuid.uuid4().hex
        seen.add(uid(n))
