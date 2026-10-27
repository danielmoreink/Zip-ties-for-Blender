"""Regression: moving the last tie above its neighbours must not rewire strands."""
import bpy
import sys
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing

addon.register()
tree = bpy.data.node_groups.new('Stable Tie Order','GeometryNodeTree')
tree.use_fake_user = True
for i in range(4):
    tree.interface.new_socket(name=f'Lane {i}',in_out='OUTPUT',socket_type='NodeSocketFloat')
target = tree.nodes.new('NodeGroupOutput')
target.location = (500,-200)
sources = [tree.nodes.new('ShaderNodeValue') for _ in range(4)]
for i,node in enumerate(sources):
    node.location = (-400,150-i*150)
    tree.links.new(node.outputs[0],target.inputs[i])
keys = [data.link_key(l,True) for l in tree.links]
ties = []
for pos in [[0,200],[250,-100],[350,-120]]:
    ties.append(data.new_tie(pos,.2,keys,ties,[.8,.7,.5,1]))
    data.write(tree,ties)
expected = [t['id'] for t in ties]

def sequence(key):
    result = []
    for link in routing.path(tree,key):
        node = link.to_node
        if routing.managed(node) and node.get(routing.SLOT)==1:
            result.append(node[routing.TIE])
    return result

assert all(sequence(k)==expected for k in keys)
original_edges = {l.as_pointer() for l in tree.links}
original_nodes = {n.as_pointer() for n in tree.nodes}
for y in range(-120,901,20):
    ties[-1]['pos'] = [350,y]
    data.write(tree,ties)
    assert all(sequence(k)==expected for k in keys), f'Route flipped at y={y}'
    assert {l.as_pointer() for l in tree.links}==original_edges, 'Moving must not recreate edges'
    assert {n.as_pointer() for n in tree.nodes}==original_nodes
# Cross horizontally as well: crossing a neighbour does not change topology.
ties[-1]['pos'] = [-600,1000]
data.write(tree,ties)
assert all(sequence(k)==expected for k in keys)
assert {l.as_pointer() for l in tree.links}==original_edges
ties[-1]['pos'] = [350,-120]
data.write(tree,ties)
inserted = data.new_tie([100,100],0,keys,ties,[1,0,0,1])
ties.append(inserted)
data.write(tree,ties)
expected.insert(1,inserted['id'])
assert all(sequence(k)==expected for k in keys), 'New tie must insert into the nearest span'
# Persistence: native chain order, rather than transient pointer state, is authoritative.
file = root/'tests'/'stable-route-order.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file))
addon.unregister()
bpy.ops.wm.open_mainfile(filepath=str(file))
tree = bpy.data.node_groups['Stable Tie Order']
addon.register()
ties = data.read(tree)
ties[2]['pos'] = [350,1000]
data.write(tree,ties)
assert all(sequence(k)==expected for k in keys)
addon.unregister()
result = dict(upward_drag=True,horizontal_crossing=True,four_strands=True,
              no_edge_recreation=True,new_tie_insertion=True,save_reload=True,visual_ui_tested=False)
(root/'tests'/'stable-order-results.json').write_text(json.dumps(result,indent=2))
print('STABLE_ROUTE_ORDER_PASS',json.dumps(result))
