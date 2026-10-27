import bpy
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing
addon.register()
tree = bpy.data.node_groups.new('Undo Reroutes','GeometryNodeTree')
tree.use_fake_user = True
a = tree.nodes.new('ShaderNodeValue')
b = tree.nodes.new('ShaderNodeMath')
link = tree.links.new(a.outputs[0],b.inputs[0])
key = data.link_key(link,True)
bpy.context.preferences.edit.use_global_undo = True
bpy.ops.ed.undo_push(message='Before ties')
tie = data.new_tie([20,30],0,[key],[],[1,0,0,1])
data.write(tree,[tie])
bpy.ops.ed.undo_push(message='Create tie')
tie['pos'] = [80,90]
data.write(tree,[tie])
bpy.ops.ed.undo_push(message='Move tie')
bpy.ops.ed.undo()
tree = bpy.data.node_groups['Undo Reroutes']
assert data.read(tree)[0]['pos'] == [20,30]
assert len(routing.path(tree,key)) == 4
bpy.ops.ed.undo()
tree = bpy.data.node_groups['Undo Reroutes']
assert len(tree.nodes) == 2 and len(tree.links) == 1 and not data.read(tree)
bpy.ops.ed.redo()
tree = bpy.data.node_groups['Undo Reroutes']
assert len(tree.nodes) == 5 and len(routing.path(tree,key)) == 4
addon.unregister()
(root/'tests'/'undo-results.json').write_text('{"undo_create":true,"undo_move":true,"redo_create":true}')
print('REROUTE_UNDO_PASS')
