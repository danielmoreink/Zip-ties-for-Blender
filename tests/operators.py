import bpy
import sys
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,selection,interaction

addon.register()
tree = bpy.data.node_groups.new('Operator Test','GeometryNodeTree')
source = tree.nodes.new('ShaderNodeValue')
target = tree.nodes.new('ShaderNodeMath')
link = tree.links.new(source.outputs[0],target.inputs[0])
key = data.link_key(link,True)
tie = data.new_tie([50,50],0,[key],[],[.5,.5,.5,1])
data.write(tree,[tie])
area = bpy.context.screen.areas[0]
area.type = 'NODE_EDITOR'
area.ui_type = 'GeometryNodeTree'
area.spaces.active.pin = True
area.spaces.active.node_tree = tree
region = next(r for r in area.regions if r.type == 'WINDOW')
with bpy.context.temp_override(area=area,region=region):
    x_item = next(item for _,item in interaction.keymaps if item.type=='X' and item.idname=='node.zip_tie_edit')
    assert x_item.properties.action=='DELETE' and not x_item.properties.delete_nodes
    selection.of(tree).add(tie['id'])
    assert bpy.ops.node.zip_tie_edit(action='ROTATE',angle=1.25) == {'FINISHED'}
    assert data.read(tree)[0]['angle'] == 1.25
    assert bpy.ops.node.zip_tie_color(color=(1,0,0,1)) == {'FINISHED'}
    assert data.read(tree)[0]['color'] == [1,0,0,1]
    # Context remove affects ties; selected computational nodes stay intact.
    source.select = target.select = True
    assert bpy.ops.node.zip_tie_edit(action=x_item.properties.action,delete_nodes=x_item.properties.delete_nodes) == {'FINISHED'}
    assert len(tree.nodes) == 2 and len(tree.links) == 1 and not data.read(tree)
    # No tie selection leaves normal Blender key handling available.
    assert bpy.ops.node.zip_tie_edit(action='DELETE',delete_nodes=False) == {'PASS_THROUGH'}
    data.write(tree,[tie])
    selection.of(tree).add(tie['id'])
    # Keyboard delete includes both native nodes and ties.
    assert bpy.ops.node.zip_tie_edit(action='DELETE',delete_nodes=True) == {'FINISHED'}
    assert len(tree.nodes) == 0 and not data.read(tree)
addon.unregister()
result = dict(rotation=True,color=True,tie_only_delete=True,x_shortcut=True,no_selection_pass_through=True,mixed_delete=True,ui_undo_tested=False)
(root/'tests'/'operator-results.json').write_text(json.dumps(result,indent=2))
print('OPERATORS_PASS',json.dumps(result))
