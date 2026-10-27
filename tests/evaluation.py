import bpy
import sys
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties
from node_zip_ties import data

node_zip_ties.register()
tree = bpy.data.node_groups.new('Evaluated Zip Ties','GeometryNodeTree')
tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
cube = tree.nodes.new('GeometryNodeMeshCube')
xyz = tree.nodes.new('ShaderNodeCombineXYZ')
xyz.inputs[0].default_value = 2.5
value = tree.nodes.new('ShaderNodeValue')
value.outputs[0].default_value = 1.5
transform = tree.nodes.new('GeometryNodeTransform')
out = tree.nodes.new('NodeGroupOutput')
reroute = tree.nodes.new('NodeReroute')
tree.links.new(cube.outputs['Mesh'],reroute.inputs[0])
tree.links.new(reroute.outputs[0],transform.inputs['Geometry'])
tree.links.new(xyz.outputs[0],transform.inputs['Translation'])
tree.links.new(value.outputs[0],transform.inputs['Scale'])
tree.links.new(transform.outputs[0],out.inputs[0])
mesh = bpy.data.meshes.new('Input')
obj = bpy.data.objects.new('Evaluation subject',mesh)
bpy.context.scene.collection.objects.link(obj)
modifier = obj.modifiers.new('Geometry Nodes','NODES')
modifier.node_group = tree


def evaluated():
    bpy.context.view_layer.update()
    result = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    output = result.to_mesh()
    try:
        return ([tuple(round(v,6) for v in vert.co) for vert in output.vertices],
                [tuple(p.vertices) for p in output.polygons])
    finally:
        result.to_mesh_clear()


before = evaluated()
assert len(before[0]) == 8 and len(before[1]) == 6
keys = [data.link_key(l,True) for l in tree.links]
tie = data.new_tie([0,0],0,keys[:4],[],[.6,.3,.2,1])
data.write(tree,[tie])
assert evaluated() == before
tie['pos'] = [200,75]
tie['angle'] = 1.57
tie['scale'] = 2.25
data.write(tree,[tie,data.new_tie([500,-20],.5,keys[:4],[tie],[0,1,0,1])])
assert evaluated() == before
node_zip_ties.unregister()
assert evaluated() == before
result = dict(blender=bpy.app.version_string,vertices=8,polygons=6,
              equal_before_after_storage=True,equal_after_move_rotate_multiple_ties=True,
              equal_after_scale=True,equal_after_disable=True,reroute=True,native_reroute_backend=True,ui_visual_tested=False)
(root/'tests'/'evaluation-results.json').write_text(json.dumps(result,indent=2))
print('EVALUATION_PASS',json.dumps(result))
