"""Background integration tests for stock-Blender native link routing."""
import bpy
import sys
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import node_zip_ties as addon
from node_zip_ties import data,routing,geometry as g,sockets

addon.register()
tree = bpy.data.node_groups.new('Reroute Backend','GeometryNodeTree')
tree.use_fake_user = True
sources = [tree.nodes.new('ShaderNodeValue') for _ in range(3)]
target = tree.nodes.new('ShaderNodeCombineXYZ')
for i,n in enumerate(sources):
    n.location = (-400,i*150)
    tree.links.new(n.outputs[0],target.inputs[i])
target.location = (400,0)
keys = [data.link_key(l,True) for l in tree.links]
first = data.new_tie([0,0],0,keys,[],[1,0,0,1])
data.write(tree,[first])
assert len(tree.nodes) == 13  # 4 real nodes + 3 helpers per strand.
assert len(tree.links) == 12
for key in keys:
    chain = routing.path(tree,key)
    assert len(chain) == 4
    assert not any(data.physical_key(l) == key for l in tree.links), 'No original bypass noodle'
before = {n.as_pointer() for n in tree.nodes if routing.managed(n)}
first['pos'] = [100,75]
first['angle'] = math.pi/2
data.write(tree,[first])
assert {n.as_pointer() for n in tree.nodes if routing.managed(n)} == before, 'Moves reuse nodes'
for key in keys:
    centre,tangent = g.lane(first,key,8)
    nodes = sorted([n for n in tree.nodes if n.get(routing.OWNER)==key],key=lambda n:n[routing.SLOT])
    for i,n in enumerate(nodes):
        expected = g.add(centre,g.mul(tangent,[-12,0,12][i]))
        actual = tuple(n.location_absolute)
        assert all(abs(actual[k]-expected[k]) < .001 for k in (0,1))
        assert sockets.socket_position(n,n.inputs[0]) == actual
# Native reroute centres and the drawn strap must share the same centre.
middle = [n for n in tree.nodes if n.get(routing.TIE)==first['id'] and n.get(routing.SLOT)==1]
native_centre = [sum(n.location_absolute[k] for n in middle)/len(middle) for k in (0,1)]
strap = g.marker(first,8,8)[0]
strap_centre = [sum(v[k] for v in strap)/4 for k in (0,1)]
assert all(abs(native_centre[k]-strap_centre[k]) < .001 for k in (0,1))
second = data.new_tie([200,50],.7,list(reversed(keys)),[first],[0,1,0,1])
data.write(tree,[first,second])
assert all(len(routing.path(tree,k)) == 7 for k in keys)
assert second['members'] == first['members']
data.write(tree,[second])
assert all(len(routing.path(tree,k)) == 4 for k in keys)
assert len(tree.nodes) == 13
data.write(tree,[])
assert len(tree.nodes) == 4 and len(tree.links) == 3
assert {data.physical_key(l) for l in tree.links} == set(keys)

# Muted connection remains muted when routed and untied.
tree.links[0].is_muted = True
muted_key = data.link_key(tree.links[0])
data.write(tree,[first])
assert all(l.is_muted for l in routing.path(tree,muted_key))
data.write(tree,[])
assert next(l for l in tree.links if data.link_key(l)==muted_key).is_muted

# A manually cut managed path must never be silently reconnected.
data.write(tree,[first])
tree.links.remove(routing.path(tree,keys[1])[1])
remaining = data.prune(tree,data.read(tree))
assert keys[1] not in remaining[0]['members']
data.write(tree,remaining)
assert not routing.path(tree,keys[1])

# Multi-input order is preserved when replacing a connection through helpers.
multi = bpy.data.node_groups.new('Multi Input Order','GeometryNodeTree')
join = multi.nodes.new('GeometryNodeJoinGeometry')
cubes = [multi.nodes.new('GeometryNodeMeshCube') for _ in range(3)]
for cube in cubes:
    multi.links.new(cube.outputs['Mesh'],join.inputs['Geometry'])
original_order = [data.link_key(l,True) for l in sorted(multi.links,key=lambda l:l.multi_input_sort_id)]
t = data.new_tie([0,0],0,original_order,[],[1,0,0,1])
data.write(multi,[t])
current = [data.link_key(l) for l in sorted([l for l in multi.links if l.to_node==join],key=lambda l:l.multi_input_sort_id)]
assert current == original_order, (current,original_order)
data.write(multi,[])
assert [data.link_key(l) for l in sorted(multi.links,key=lambda l:l.multi_input_sort_id)] == original_order

# Overlay-only 0.1 data migrates without changing the stored tie IDs.
legacy = bpy.data.node_groups.new('Legacy Overlay Migration','GeometryNodeTree')
legacy.use_fake_user = True
la = legacy.nodes.new('ShaderNodeValue')
lb = legacy.nodes.new('ShaderNodeMath')
ll = legacy.links.new(la.outputs[0],lb.inputs[0])
lk = data.link_key(ll,True)
lt = data.new_tie([10,20],0,[lk],[],[1,0,0,1])
legacy[data.KEY] = json.dumps(dict(version=1,ties=[lt]))
addon.migrate_routes()
assert len(legacy.nodes) == 5 and len(routing.path(legacy,lk)) == 4
assert data.read(legacy)[0]['id'] == lt['id']
addon.migrate_routes()
assert len(legacy.nodes) == 5

# Upgrade 0.2.0's offset helper positions while retaining tie position and IDs.
for n in legacy.nodes:
    if routing.managed(n):
        n.location.x -= 5
        n.location.y += 5
del legacy[routing.LAYOUT_KEY]
old_helper_ids = {n.as_pointer() for n in legacy.nodes if routing.managed(n)}
addon.migrate_routes()
assert legacy[routing.LAYOUT_KEY] == routing.LAYOUT_VERSION
assert {n.as_pointer() for n in legacy.nodes if routing.managed(n)} == old_helper_ids
centre_node = next(n for n in legacy.nodes if n.get(routing.SLOT)==1)
assert tuple(centre_node.location_absolute) == tuple(lt['pos'])

# Native reroutes also work in embedded Shader and standalone Compositor trees.
material = bpy.data.materials.new('Shader Bundle')
material.use_nodes = True
shader = material.node_tree
sa = shader.nodes.new('ShaderNodeValue')
sb = shader.nodes.new('ShaderNodeMath')
sl = shader.links.new(sa.outputs[0],sb.inputs[0])
sk = data.link_key(sl,True)
st = data.new_tie([0,0],0,[sk],[],[1,0,0,1])
data.write(shader,[st])
assert len(routing.path(shader,sk)) == 4
data.write(shader,[])
assert len(routing.path(shader,sk)) == 1
comp = bpy.data.node_groups.new('Compositor Bundle','CompositorNodeTree')
comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
ca = comp.nodes.new('CompositorNodeRGB')
cb = comp.nodes.new('NodeGroupOutput')
cl = comp.links.new(ca.outputs[0],cb.inputs[0])
ck = data.link_key(cl,True)
ct = data.new_tie([0,0],0,[ck],[],[1,0,0,1])
data.write(comp,[ct])
assert len(routing.path(comp,ck)) == 4
data.write(comp,[])
assert len(routing.path(comp,ck)) == 1

# Saved native helpers and connections survive without registered extension classes.
data.write(tree,remaining)
saved_links = len(tree.links)
saved_nodes = len(tree.nodes)
file = root/'tests'/'reroute-backend.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file))
addon.unregister()
bpy.ops.wm.open_mainfile(filepath=str(file))
restored = bpy.data.node_groups['Reroute Backend']
assert len(restored.links) == saved_links and len(restored.nodes) == saved_nodes
assert all(routing.path(restored,k) for k in remaining[0]['members'])
result = dict(blender=bpy.app.version_string,three_strands=True,no_bypass_links=True,
              move_rotate_reuse_nodes=True,multiple_ties=True,remove_restores_direct=True,
              cut_not_resurrected=True,muted_preserved=True,multi_input_order=True,
              legacy_migration=True,centred_strap=True,offset_layout_upgrade=True,shader=True,compositor=True,
              save_reload_without_addon=True,ui_visual_tested=False)
(root/'tests'/'reroute-results.json').write_text(json.dumps(result,indent=2))
print('REROUTE_BACKEND_PASS',json.dumps(result))
