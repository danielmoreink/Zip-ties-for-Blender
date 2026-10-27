import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from . import data, geometry as g, selection, sockets
from .preferences import prefs

handles = []
last_error = ''


def tree_of(context):
    space = context.space_data
    return space.edit_tree if space and space.type == 'NODE_EDITOR' else None


def shown(tree, ties):
    live = {data.link_key(l) for l in tree.links if not l.is_hidden}
    return [t for t in ties if any(k in live for k in t['members'])]


def line(points, color, width=2):
    if len(points) < 2:
        return
    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float('viewportSize', gpu.state.viewport_get()[2:])
    shader.uniform_float('lineWidth', width)
    shader.uniform_float('color', color)
    batch_for_shader(shader,'LINE_STRIP',{'pos':points}).draw(shader)


def polygon(points,color,shades=None):
    shader = gpu.shader.from_builtin('SMOOTH_COLOR' if shades else 'UNIFORM_COLOR')
    shader.bind()
    attributes = {'pos':points}
    if shades:
        attributes['color'] = [tuple(c*shade for c in color[:3])+(color[3],) for shade in shades]
    else:
        shader.uniform_float('color', color)
    indices = [(0,i,i+1) for i in range(1,len(points)-1)]
    batch_for_shader(shader,'TRIS',attributes,indices=indices).draw(shader)


def draw_tie(tie,spacing,width,transform,border,active):
    strap,collar,tip,front = g.marker(tie,spacing,width)
    tangent,normal = g.axes(tie['angle'])
    h = g.half_length(tie,spacing)
    # Smooth body shadows at the lower end and immediately below the collar.
    stops = [(0,.48),(.2,1),(.78,1),(1,.55)]
    for (u,shade),(v,next_shade) in zip(stops,stops[1:]):
        a,b = -h+2*h*u,-h+2*h*v
        local = [(-width/2,a),(width/2,a),(width/2,b),(-width/2,b)]
        points = [transform(g.add(tie['pos'],g.add(g.mul(tangent,x),g.mul(normal,y)))) for x,y in local]
        polygon(points,tie['color'],[shade,shade,next_shade,next_shade])
    line([transform(p) for p in strap+strap[:1]],border,2 if active else 1.3)
    for index,poly in enumerate((collar,tip,front)):
        points = [transform(p) for p in poly]
        shades = None
        if index==1:
            shades = [.48+.52*max(0,min(1,(g.dot(g.sub(p,tie['pos']),normal)-h-.05*width)/(1.65*width))) for p in poly]
        polygon(points,tie['color'],shades)
        line(points+points[:1],border,2 if active else 1.3)


def draw():
    global last_error
    context = bpy.context
    tree = tree_of(context)
    if not tree or not prefs(context).enabled:
        return
    options = prefs(context)
    ties = shown(tree,data.read(tree))
    transform = lambda p: sockets.to_region(context,p)
    stroke = selection.preview.get(context.area.as_pointer())
    cuts = stroke[2] if stroke else set()
    gpu.state.blend_set('ALPHA')
    try:
        for tie in ties:
            active = tie['id'] in selection.of(tree) or tie['id'] == selection.hovered.get(context.area.as_pointer())
            border = (1,.1,.1,1) if tie['id'] in cuts else (1,1,1,1) if active else (.05,.05,.05,1)
            draw_tie(tie,options.spacing,options.width,transform,border,active)
        if stroke:
            line([transform(stroke[0]),transform(stroke[1])],(1,.1,.1,1) if cuts else (1,1,1,1))
        box = selection.boxes.get(context.area.as_pointer())
        if box:
            a,b = box
            vertices = [a,(b[0],a[1]),b,(a[0],b[1]),a]
            line([transform(p) for p in vertices],(.65,.8,1,1),1)
        last_error = ''
    except Exception as exc:
        # Surface diagnostics once in UI, rather than flooding Blender's console every frame.
        last_error = f'{type(exc).__name__}: {exc}'
    finally:
        gpu.state.blend_set('NONE')


def register():
    handles.append(bpy.types.SpaceNodeEditor.draw_handler_add(draw,(), 'WINDOW','POST_PIXEL'))


def unregister():
    for handle in handles:
        bpy.types.SpaceNodeEditor.draw_handler_remove(handle,'WINDOW')
    handles.clear()
