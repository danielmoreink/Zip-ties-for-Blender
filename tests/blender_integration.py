"""Execute with Blender --background --factory-startup --python this-file."""
import bpy
import sys
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,selection,routing

addon.register()
tree = bpy.data.node_groups.new('Zip Ties Integration','GeometryNodeTree')
tree.use_fake_user = True
a = tree.nodes.new('ShaderNodeValue')
b = tree.nodes.new('ShaderNodeValue')
c = tree.nodes.new('ShaderNodeValue')
destination = tree.nodes.new('ShaderNodeCombineXYZ')
for i,node in enumerate([a,b,c]):
    tree.links.new(node.outputs[0],destination.inputs[i])
keys = [data.link_key(l,True) for l in tree.links]
tie = data.new_tie([20,30],0,keys,[],[.4,.5,.6,1])
data.write(tree,[tie])
assert data.read(tree) == [tie]
a.name = 'Renamed after tying'
assert routing.path(tree,keys[0])
frame = tree.nodes.new('NodeFrame')
a.parent = frame
a.location = (123,456)
assert routing.path(tree,keys[0])
second = data.new_tie([40,50],1,list(reversed(keys)),[tie],[1,0,0,1])
assert second['members'] == keys
data.write(tree,[tie,second])
assert routing.live_keys(tree) == set(keys)
# A disconnected/reconnected connection retains identity.
link = routing.path(tree,keys[0])[-1]
src,dst = link.from_socket,link.to_socket
old_key = data.link_key(link)
tree.links.remove(link)
new = tree.links.new(src,dst)
assert data.link_key(new) == old_key
# Socket identifier, not socket display name, carries membership.
src.name = 'Display name changed'
assert data.link_key(new) == old_key
removed = next(l for l in tree.links if data.link_key(l) == keys[1])
tree.links.remove(removed)
pruned = data.prune(tree,data.read(tree))
assert all(keys[1] not in t['members'] for t in pruned)
# Malformed and unsupported versions are safely ignored.
saved = tree[data.KEY]
for raw in ['garbage','[]','{"version":99,"ties":[]}', '{"version":1,"ties":[null]}']:
    tree[data.KEY] = raw
    assert data.read(tree) == []
tree[data.KEY] = saved
# Same data survives a real .blend save/reload without registered classes.
path = root/'tests'/'integration.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
expected = data.read(tree)
addon.unregister()
assert not selection.selected
bpy.ops.wm.open_mainfile(filepath=str(path))
assert data.read(bpy.data.node_groups['Zip Ties Integration']) == expected
addon.register()
addon.unregister()
result = dict(blender=bpy.app.version_string,uses_native_reroutes=True,
              graph_integrity=True,rename=True,frames=True,reconnect=True,prune=True,
              save_reload_without_extension=True,registration_cleanup=True)
(root/'tests'/'blender-results.json').write_text(json.dumps(result,indent=2))
print('ZIP_TIES_INTEGRATION_PASS',json.dumps(result))
