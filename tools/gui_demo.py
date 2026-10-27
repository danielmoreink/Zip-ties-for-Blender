import bpy
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import addon_utils
addon_utils.enable('node_zip_ties',default_set=True)
from node_zip_ties import data
tree = bpy.data.node_groups.new('Node Zip Ties • Native reroutes','GeometryNodeTree')
tree.use_fake_user = True
tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
cube = tree.nodes.new('GeometryNodeMeshCube')
cube.location = (-420,200)
vector = tree.nodes.new('ShaderNodeCombineXYZ')
vector.location = (-420,-60)
value = tree.nodes.new('ShaderNodeValue')
value.location = (-420,-290)
value.outputs[0].default_value = 1
transform = tree.nodes.new('GeometryNodeTransform')
transform.location = (220,120)
output = tree.nodes.new('NodeGroupOutput')
output.location = (480,120)
tree.links.new(cube.outputs['Mesh'],transform.inputs['Geometry'])
tree.links.new(vector.outputs[0],transform.inputs['Translation'])
tree.links.new(value.outputs[0],transform.inputs['Scale'])
tree.links.new(transform.outputs['Geometry'],output.inputs['Geometry'])
keys = [data.link_key(l,True) for l in list(tree.links)[:3]]
ties = [data.new_tie([x,20],angle,keys,[],[.95,.55,.15,1]) for x,angle in [(-70,0),(100,.25)]]
data.write(tree,ties)
area = max(bpy.context.screen.areas,key=lambda a:a.width*a.height)
area.type = 'NODE_EDITOR'
area.ui_type = 'GeometryNodeTree'
space = area.spaces.active
space.pin = True
space.node_tree = tree
space.show_region_ui = True
for node in tree.nodes:
    node.select = True
def frame():
    with bpy.context.temp_override(area=area,region=next(r for r in area.regions if r.type=='WINDOW')):
        bpy.ops.node.view_all()
    return None
bpy.app.timers.register(frame,first_interval=2)
