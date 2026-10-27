"""S scales strap length and native lane gaps, with persistence and rollback."""
import bpy
import sys
import math
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing,selection,interaction,geometry as g
addon.register()
tree=bpy.data.node_groups.new('Scale Modal','GeometryNodeTree')
tree.use_fake_user=True
target=tree.nodes.new('ShaderNodeCombineXYZ')
sources=[tree.nodes.new('ShaderNodeValue') for _ in range(3)]
for i,node in enumerate(sources):
    tree.links.new(node.outputs[0],target.inputs[i])
keys=[data.link_key(l,True) for l in tree.links]
tie=data.new_tie([0,0],.3,keys,[],[1,0,0,1])
other=data.new_tie([300,0],0,keys,[tie],[0,1,0,1])
data.write(tree,[tie,other])
selection.of(tree).add(tie['id'])
original=data.read(tree)
edges={l.as_pointer() for l in tree.links}
nodes={n.as_pointer() for n in tree.nodes}
status=[]
ctx=SimpleNamespace(space_data=SimpleNamespace(type='NODE_EDITOR',edit_tree=tree),
    preferences=bpy.context.preferences,workspace=SimpleNamespace(status_text_set=status.append),
    window_manager=SimpleNamespace(modal_handler_add=lambda op:None,windows=[]))
class Scale:
    invoke=interaction.NZT_OT_scale.invoke
    modal=interaction.NZT_OT_scale.modal
    update=interaction.NZT_OT_scale.update
    status=interaction.NZT_OT_scale.status
    finish=interaction.NZT_OT_scale.finish
def event(kind='MOUSEMOVE',pos=(100,0),value='NOTHING'):
    return SimpleNamespace(type=kind,pos=pos,value=value)
def current():
    return next(t for t in data.read(tree) if t['id']==tie['id'])
def gap():
    lane_nodes=sorted([n for n in tree.nodes if n.get(routing.TIE)==tie['id'] and n.get(routing.SLOT)==1],key=lambda n:n[routing.OWNER])
    return sorted(math.hypot(*g.sub(a.location_absolute,b.location_absolute)) for i,a in enumerate(lane_nodes) for b in lane_nodes[i+1:])

oldgap=gap()
oldlength=2*g.half_length(tie,8)
with patch.object(interaction,'point',side_effect=lambda context,e:e.pos):
    op=Scale()
    assert op.invoke(ctx,event('S',value='PRESS'))=={'RUNNING_MODAL'}
    op.modal(ctx,event(pos=(200,0)))
    scaled=current()
    assert scaled['scale']==2
    assert abs(2*g.half_length(scaled,8)-2*oldlength)<1e-6
    assert all(abs(a-2*b)<1e-4 for a,b in zip(gap(),oldgap))
    assert scaled['pos']==tie['pos'] and scaled['angle']==tie['angle']
    before=g.marker(tie,8,8)[0]
    after=g.marker(scaled,8,8)[0]
    assert abs(math.hypot(*g.sub(before[1],before[0]))-math.hypot(*g.sub(after[1],after[0])))<1e-6
    assert 'scale' not in data.read(tree)[1], 'Unselected tie must remain unchanged'
    assert op.modal(ctx,event('ESC',value='PRESS'))=={'CANCELLED'}
    assert data.read(tree)==original
    # Numeric entry supports S .5 Enter without forcing mouse movement.
    op=Scale()
    op.invoke(ctx,event('S',value='PRESS'))
    op.modal(ctx,event('PERIOD',value='PRESS'))
    op.modal(ctx,event('FIVE',value='PRESS'))
    assert current()['scale']==.5
    assert op.modal(ctx,event('RET',value='PRESS'))=={'FINISHED'}
    assert status[-1] is None
    # Centre invocation can both shrink and grow without a zero denominator.
    op=Scale()
    op.invoke(ctx,event('S',pos=(0,0),value='PRESS'))
    op.modal(ctx,event(pos=(-16,0)))
    assert .1<=current()['scale']<.5
    op.modal(ctx,event('RIGHTMOUSE',value='PRESS'))
    assert current()['scale']==.5
    selection.of(tree).clear()
    with patch.object(interaction,'hit_at',return_value=None):
        assert Scale().invoke(ctx,event('S',value='PRESS'))=={'PASS_THROUGH'}

assert {l.as_pointer() for l in tree.links}==edges
assert {n.as_pointer() for n in tree.nodes}==nodes
assert any(item.idname=='node.zip_tie_scale' and item.type=='S' for _,item in interaction.keymaps)
file=root/'tests'/'scale-modal.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file))
addon.unregister()
bpy.ops.wm.open_mainfile(filepath=str(file))
tree=bpy.data.node_groups['Scale Modal']
assert current()['scale']==.5
assert all(len(routing.path(tree,key))==7 for key in keys)
result=dict(mouse_scale=True,numeric_half=True,proportional_length_and_gaps=True,width_unchanged=True,
            centre_and_angle_unchanged=True,selected_only=True,cancel_restores=True,centre_start=True,
            no_rewiring=True,save_reload=True,s_keymap=True,real_ui_dispatch_tested=False)
(root/'tests'/'scale-results.json').write_text(json.dumps(result,indent=2))
print('SCALE_MODAL_PASS',json.dumps(result))
