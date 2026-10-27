"""G / GG movement contracts using real Blender reroutes and modal test events."""
import bpy
import sys
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing,selection,interaction,transforms

addon.register()
tree = bpy.data.node_groups.new('Move and Slide','GeometryNodeTree')
target = tree.nodes.new('ShaderNodeCombineXYZ')
target.location = (800,0)
sources = [tree.nodes.new('ShaderNodeValue') for _ in range(3)]
for i,node in enumerate(sources):
    node.location = (-400,i*100)
    tree.links.new(node.outputs[0],target.inputs[i])
keys = [data.link_key(l,True) for l in tree.links]
ties=[]
for x in [0,200,400]:
    ties.append(data.new_tie([x,0],0,keys,ties,[1,0,0,1]))
    data.write(tree,ties)
middle = ties[1]
selection.of(tree).add(middle['id'])
original = data.read(tree)
node_ids = {n.as_pointer() for n in tree.nodes}
edge_ids = {l.as_pointer() for l in tree.links}
status=[]
ctx = SimpleNamespace(space_data=SimpleNamespace(type='NODE_EDITOR',edit_tree=tree),
    preferences=bpy.context.preferences,workspace=SimpleNamespace(status_text_set=status.append),
    window_manager=SimpleNamespace(modal_handler_add=lambda op:None,windows=[]))
class Move:
    invoke=interaction.NZT_OT_move.invoke
    modal=interaction.NZT_OT_move.modal
    update=interaction.NZT_OT_move.update
    finish=interaction.NZT_OT_move.finish
    status=interaction.NZT_OT_move.status
class Drag:
    invoke=interaction.NZT_OT_pick.invoke
    modal=interaction.NZT_OT_pick.modal
def event(kind='MOUSEMOVE',pos=(200,0),value='NOTHING',**kw):
    return SimpleNamespace(type=kind,pos=pos,value=value,shift=False,alt=False,ctrl=False,**kw)
def current():
    return next(t for t in data.read(tree) if t['id']==middle['id'])

with patch.object(interaction,'point',side_effect=lambda context,e:e.pos):
    op=Move()
    assert op.invoke(ctx,event('G',value='PRESS'))=={'RUNNING_MODAL'}
    op.modal(ctx,event(pos=(250,80)))
    assert current()['pos']==[250,80]
    assert op.modal(ctx,event('ESC',value='PRESS'))=={'CANCELLED'}
    assert data.read(tree)==original
    op=Move()
    op.invoke(ctx,event('G',value='PRESS'))
    # Key-repeat must not be mistaken for a second deliberate press.
    op.modal(ctx,event('G',value='PRESS',is_repeat=True))
    assert not op.slide
    op.modal(ctx,event('G',value='PRESS'))
    assert op.slide and current()['pos']==middle['pos'], 'GG must not jump at rest'
    op.modal(ctx,event(pos=(290,100)))
    assert abs(current()['pos'][0]-290)<.01 and abs(current()['pos'][1])<.001
    op.modal(ctx,event(pos=(10000,10000)))
    assert 200<current()['pos'][0]<400-24, 'Cannot pass the next tie'
    op.modal(ctx,event(pos=(-10000,-10000)))
    assert 24<current()['pos'][0]<200, 'Cannot pass the previous tie'
    assert op.modal(ctx,event('RIGHTMOUSE',value='PRESS'))=={'CANCELLED'}
    assert data.read(tree)==original
    # Switching after a free move still uses the original frozen noodle guide.
    op=Move()
    op.invoke(ctx,event('G',value='PRESS'))
    op.modal(ctx,event(pos=(260,90)))
    op.modal(ctx,event('G',value='PRESS'))
    assert abs(current()['pos'][0]-260)<.01 and abs(current()['pos'][1])<.001
    assert op.modal(ctx,event('RET',value='PRESS'))=={'FINISHED'}
    assert status[-1] is None
    data.write(tree,original)
    # Existing ordinary click-and-drag is deliberately unchanged.
    with patch.object(interaction,'hit_at',return_value=middle):
        drag=Drag()
        assert drag.invoke(ctx,event('LEFTMOUSE',value='PRESS'))=={'RUNNING_MODAL'}
        drag.modal(ctx,event(pos=(225,40)))
        assert current()['pos']==[225,40]
        assert drag.modal(ctx,event('LEFTMOUSE',value='RELEASE'))=={'FINISHED'}
    data.write(tree,original)
    # Frozen curved guides follow the existing noodle rather than a straight axis.
    curved=data.read(tree)
    curved[0]['pos']=[0,160]
    curved[2]['pos']=[400,160]
    data.write(tree,curved)
    guide=transforms.slide_guide(tree,curved[1],ctx)
    assert tuple(curved[1]['pos']) in guide
    projected=transforms.project(guide,(300,120))
    assert 200<projected[0]<400 and projected[1]>0
    assert transforms.project(guide,(100000,100000)) in guide, 'Far motion clamps to a guide endpoint'
    data.write(tree,original)
    selection.of(tree).clear()
    with patch.object(interaction,'hit_at',return_value=None):
        assert Move().invoke(ctx,event('G',value='PRESS'))=={'PASS_THROUGH'}

assert {n.as_pointer() for n in tree.nodes}==node_ids
assert {l.as_pointer() for l in tree.links}==edge_ids
assert any(item.idname=='node.zip_tie_move' and item.type=='G' for _,item in interaction.keymaps)
addon.unregister()
result=dict(g_free_move=True,gg_slide=True,neighbour_limits=True,curved_guide=True,cancel_restores=True,
            confirm=True,key_repeat_ignored=True,click_drag_retained=True,no_rewiring=True,
            no_selection_pass_through=True,real_ui_dispatch_tested=False)
(root/'tests'/'move-results.json').write_text(json.dumps(result,indent=2))
print('MOVE_MODAL_PASS',json.dumps(result))
