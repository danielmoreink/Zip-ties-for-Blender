"""Exercise the R operator's modal events against real Blender reroute graphs."""
import bpy
import sys
import math
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing,selection,interaction

addon.register()
tree = bpy.data.node_groups.new('Modal Rotation','GeometryNodeTree')
a = tree.nodes.new('ShaderNodeValue')
b = tree.nodes.new('ShaderNodeMath')
key = data.link_key(tree.links.new(a.outputs[0],b.inputs[0]),True)
tie = data.new_tie([0,0],0,[key],[],[1,0,0,1])
data.write(tree,[tie])
selection.of(tree).add(tie['id'])
helper_ids = {n.as_pointer() for n in tree.nodes if routing.managed(n)}
status = []
context = SimpleNamespace(
    space_data=SimpleNamespace(type='NODE_EDITOR',edit_tree=tree),
    preferences=bpy.context.preferences,
    workspace=SimpleNamespace(status_text_set=status.append),
    window_manager=SimpleNamespace(modal_handler_add=lambda op:None,windows=[]))
class Harness:
    invoke = interaction.NZT_OT_rotate.invoke
    track = interaction.NZT_OT_rotate.track
    modal = interaction.NZT_OT_rotate.modal
    finish = interaction.NZT_OT_rotate.finish

def event(kind='MOUSEMOVE',angle=0,value='NOTHING'):
    return SimpleNamespace(type=kind,value=value,pos=(100*math.cos(angle),100*math.sin(angle)))

with patch.object(interaction,'point',side_effect=lambda ctx,e:e.pos):
    op = Harness()
    assert op.invoke(context,event('R',value='PRESS')) == {'RUNNING_MODAL'}
    op.modal(context,event(angle=math.radians(37)))
    assert abs(data.read(tree)[0]['angle']-math.radians(37)) < 1e-6, 'R must not snap'
    assert {n.as_pointer() for n in tree.nodes if routing.managed(n)} == helper_ids
    assert len(routing.path(tree,key)) == 4
    assert op.modal(context,event('RET',value='PRESS')) == {'FINISHED'}
    assert status[-1] is None
    committed = data.read(tree)
    op = Harness()
    op.invoke(context,event('R',value='PRESS'))
    op.modal(context,event(angle=1))
    assert op.modal(context,event('ESC',value='PRESS')) == {'CANCELLED'}
    assert data.read(tree) == committed
    op = Harness()
    op.invoke(context,event('R',value='PRESS'))
    op.modal(context,event(angle=math.radians(179)))
    op.modal(context,event(angle=math.radians(-179)))
    assert abs(op.delta-math.radians(181)) < 1e-6
    assert op.modal(context,event('RIGHTMOUSE',value='PRESS')) == {'CANCELLED'}
    # The shortcut must leave Blender's normal key behavior available without ties.
    selection.of(tree).clear()
    with patch.object(interaction,'hit_at',return_value=None):
        assert Harness().invoke(context,event('R',value='PRESS')) == {'PASS_THROUGH'}
    # Hovering a tie also allows starting R without a prior click.
    with patch.object(interaction,'hit_at',return_value=committed[0]):
        op = Harness()
        assert op.invoke(context,event('R',value='PRESS')) == {'RUNNING_MODAL'}
        assert op.modal(context,event('LEFTMOUSE',value='PRESS')) == {'FINISHED'}

assert any(item.idname=='node.zip_tie_rotate' and item.type=='R' for _,item in interaction.keymaps)
addon.unregister()
result = dict(free_37_degrees=True,confirm=True,cancel_restores=True,angle_wrap=True,
              native_helpers_reused=True,no_tie_pass_through=True,hover_start=True,r_keymap=True,
              real_ui_event_dispatch_tested=False)
(root/'tests'/'rotation-results.json').write_text(json.dumps(result,indent=2))
print('ROTATION_MODAL_PASS',json.dumps(result))
