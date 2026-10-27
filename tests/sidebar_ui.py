"""UI contract regression: sidebar has no rotation; keyboard/context retain it."""
import bpy
import sys
import json
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,selection,ui,interaction,preferences,rendering
addon.register()
tree = bpy.data.node_groups.new('Sidebar UI','GeometryNodeTree')
a = tree.nodes.new('ShaderNodeValue')
b = tree.nodes.new('ShaderNodeMath')
key = data.link_key(tree.links.new(a.outputs[0],b.inputs[0]),True)
tie = data.new_tie([0,0],0,[key],[],[.8,.2,.4,1])
data.write(tree,[tie])
area = bpy.context.screen.areas[0]
area.type = 'NODE_EDITOR'
area.ui_type = 'GeometryNodeTree'
area.spaces.active.pin = True
area.spaces.active.node_tree = tree
region = next(r for r in area.regions if r.type=='WINDOW')

class Layout:
    def __init__(self,events):
        self.events=events
        self.enabled=True
    def column(self,**kw):
        return Layout(self.events)
    row=column
    def operator(self,name,**kw):
        op=SimpleNamespace()
        self.events.append((name,self.enabled,kw,op))
        return op
    def label(self,**kw): pass
    def prop(self,*args,**kw): pass
    def separator(self): pass

with bpy.context.temp_override(area=area,region=region):
    ctx=bpy.context
    selection.of(tree).clear()
    events=[]
    ui.NZT_PT_panel.draw(SimpleNamespace(layout=Layout(events)),ctx)
    assert not any(name=='node.zip_tie_rotate' or getattr(op,'action',None)=='ROTATE' for name,_,_,op in events)
    assert all(not enabled for name,enabled,_,_ in events if name in {'node.zip_tie_color','node.zip_tie_edit'})
    assert not interaction.NZT_OT_color.poll(ctx)
    selection.of(tree).add(tie['id'])
    events=[]
    for panel in [ui.NZT_PT_panel,ui.NZT_PT_appearance,ui.NZT_PT_maintenance]:
        panel.draw(SimpleNamespace(layout=Layout(events)),ctx)
    assert not any(name in {'node.zip_tie_box','node.zip_tie_move_selection','node.zip_tie_copy','node.zip_tie_paste'} for name,_,_,_ in events)
    assert not any(name=='node.zip_tie_rotate' or getattr(op,'action',None)=='ROTATE' for name,_,_,op in events)
    assert all(enabled for name,enabled,_,_ in events if name=='node.zip_tie_color')
    context_events=[]
    ui.NZT_MT_context.draw(SimpleNamespace(layout=Layout(context_events)),ctx)
    assert any(name=='node.zip_tie_rotate' for name,_,_,_ in context_events)
    assert any(getattr(op,'action',None)=='ROTATE' for _,_,_,op in context_events)
    assert any(item.idname=='node.zip_tie_rotate' and item.type=='R' for _,item in interaction.keymaps)
    # Color initialization uses the actual selection, rather than the grey default.
    harness=SimpleNamespace(color=(0,0,0,1))
    mock_ctx=SimpleNamespace(space_data=ctx.space_data,window_manager=SimpleNamespace(invoke_props_dialog=lambda op:{'RUNNING_MODAL'}))
    assert interaction.NZT_OT_color.invoke(harness,mock_ctx,None)=={'RUNNING_MODAL'}
    assert harness.color==tie['color']
    assert bpy.ops.node.zip_tie_color(color=(.1,.3,.7,1))=={'FINISHED'}
    assert abs(data.read(tree)[0]['color'][2]-.7)<1e-6
    # Visibility is presentation-only; selected ties may still be edited.
    old=preferences.DEFAULTS.enabled
    preferences.DEFAULTS.enabled=False
    assert interaction.hit_at(ctx,(0,0)) is None
    assert interaction.NZT_OT_color.poll(ctx)
    preferences.DEFAULTS.enabled=old
addon.unregister()
result=dict(sidebar_no_rotation=True,nodes_section_removed=True,r_hotkey_preserved=True,context_rotation_preserved=True,
            selected_action_states=True,color_initialization=True,color_execution=True,
            visibility_separate=True,visual_layout_tested=False)
(root/'tests'/'sidebar-results.json').write_text(json.dumps(result,indent=2))
print('SIDEBAR_UI_PASS',json.dumps(result))
