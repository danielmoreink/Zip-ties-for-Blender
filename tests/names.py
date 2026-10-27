"""Naming, persistence and screen-space label placement without GPU drawing."""
import bpy
import sys
import math
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing,selection,interaction,rendering,geometry as g,preferences
addon.register()
tree=bpy.data.node_groups.new('Named Ties','GeometryNodeTree')
tree.use_fake_user=True
a=tree.nodes.new('ShaderNodeValue')
b=tree.nodes.new('ShaderNodeMath')
key=data.link_key(tree.links.new(a.outputs[0],b.inputs[0]),True)
tie=data.new_tie([50,50],.4,[key],[],[1,0,0,1])
other=data.new_tie([200,0],0,[key],[tie],[0,1,0,1])
data.write(tree,[tie,other])
edges={l.as_pointer() for l in tree.links}
area=bpy.context.screen.areas[0]
area.type='NODE_EDITOR'
area.ui_type='GeometryNodeTree'
area.spaces.active.pin=True
area.spaces.active.node_tree=tree
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=area,region=region):
    assert not bpy.ops.node.zip_tie_name.poll()
    selection.of(tree).add(tie['id'])
    assert bpy.ops.node.zip_tie_name.poll()
    assert bpy.ops.node.zip_tie_name(name='  Main\n bundle — é  ')=={'FINISHED'}
    named=data.read(tree)[0]
    assert named['name']=='Main bundle — é'
    assert 'name' not in data.read(tree)[1]
    selection.of(tree).add(other['id'])
    assert not bpy.ops.node.zip_tie_name.poll(), 'Rename must target one tie'
    selection.of(tree).discard(other['id'])
    harness=SimpleNamespace(tie_id='',name='')
    mock_ctx=SimpleNamespace(space_data=bpy.context.space_data,
        window_manager=SimpleNamespace(invoke_props_dialog=lambda op:{'RUNNING_MODAL'}))
    assert interaction.NZT_OT_name.invoke(harness,mock_ctx,None)=={'RUNNING_MODAL'}
    assert harness.name==named['name'] and harness.tie_id==tie['id']
    font=SimpleNamespace(size=Mock(),dimensions=Mock(return_value=(100,11)),position=Mock(),
        color=Mock(),enable=Mock(),disable=Mock(),shadow=Mock(),shadow_offset=Mock(),draw=Mock(),SHADOW=1)
    # Rotated/scaled ties still get upright text above the complete silhouette.
    for angle in [0,.6,math.pi/2,math.pi]:
        named['angle']=angle
        named['scale']=2
        transform=lambda p:(p[0]*2,p[1]*2)
        points=[transform(p) for poly in g.marker(named,8,8) for p in poly]
        x,y=rendering.label_anchor(named,8,8,transform)
        assert y==max(p[1] for p in points)
        with patch.object(rendering,'blf',font):
            rendering.draw_name(bpy.context,named,preferences.DEFAULTS,transform)
        args=font.position.call_args.args
        assert abs(args[1]-(x-50))<1e-5 and args[2]>y, (args,x,y)
    assert font.draw.call_args.args[-1]=='Main bundle — é'
    assert bpy.ops.node.zip_tie_name(name='')=={'FINISHED'}
    assert 'name' not in data.read(tree)[0]
    assert bpy.ops.node.zip_tie_name(name='Saved name')=={'FINISHED'}
assert {l.as_pointer() for l in tree.links}==edges
file=root/'tests'/'named-ties.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file))
addon.unregister()
bpy.ops.wm.open_mainfile(filepath=str(file))
tree=bpy.data.node_groups['Named Ties']
assert data.read(tree)[0]['name']=='Saved name'
result=dict(rename=True,unicode=True,single_selection=True,clear_hides=True,
            above_rotated_silhouette=True,no_rewiring=True,save_reload=True,actual_font_render_tested=False)
(root/'tests'/'name-results.json').write_text(json.dumps(result,indent=2))
print('TIE_NAMES_PASS',json.dumps(result))
