import bpy
import sys
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing
addon.register()
test_temp = root/'tests'/'clipboard-temp'
test_temp.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.temporary_directory = str(test_temp)
tree = bpy.data.node_groups.new('Clipboard Reroute Test','GeometryNodeTree')
sources = [tree.nodes.new('ShaderNodeValue') for _ in range(3)]
target = tree.nodes.new('ShaderNodeCombineXYZ')
for i,source in enumerate(sources):
    source.location = (-300,150*i)
    tree.links.new(source.outputs[0],target.inputs[i])
target.location = (300,0)
keys = [data.link_key(l,True) for l in tree.links]
tie = data.new_tie([0,0],0,keys,[],[1,0,0,1])
tie['scale'] = 1.75
data.write(tree,[tie])
area = bpy.context.screen.areas[0]
area.type = 'NODE_EDITOR'
area.ui_type = 'GeometryNodeTree'
area.spaces.active.pin = True
area.spaces.active.node_tree = tree
region = next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=area,region=region):
    assert bpy.ops.node.zip_tie_copy() == {'FINISHED'}
    assert bpy.ops.node.zip_tie_paste() == {'FINISHED'}
ties = data.read(tree)
assert len(ties) == 2, len(ties)
assert len(tree.nodes) == 26, len(tree.nodes)
assert len(tree.links) == 24, len(tree.links)
assert not set(ties[0]['members']) & set(ties[1]['members'])
for t in ties:
    assert t['scale']==1.75
    assert all(len(routing.path(tree,k)) == 4 for k in t['members'])
    assert sum(1 for n in tree.nodes if n.get(routing.TIE)==t['id']) == 9
addon.unregister()
result = dict(copy_paste=True,scale_preserved=True,independent_UUIDs=True,reused_pasted_helpers=True,links=24,nodes=26)
(root/'tests'/'clipboard-results.json').write_text(json.dumps(result,indent=2))
print('CLIPBOARD_REROUTES_PASS',json.dumps(result))
