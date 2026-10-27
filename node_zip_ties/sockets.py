"""Socket estimates and View2D conversion for standard Blender node editors."""


def socket_position(node, socket):
    p = node.location_absolute
    if node.bl_idname == 'NodeReroute':
        return tuple(p)
    if node.hide:
        return (p.x + (node.width if socket.is_output else 0), p.y - 15)
    visible = [s for s in (node.outputs if socket.is_output else node.inputs)
               if not s.hide and s.enabled and not s.is_unavailable]
    index = next((i for i,s in enumerate(visible) if s == socket), 0)
    # Custom node layouts, expanded values and panels invalidate this estimate.
    return (p.x + (node.width if socket.is_output else 0), p.y - 35 - 22*index)


def controls(link, context):
    a = socket_position(link.from_node, link.from_socket)
    b = socket_position(link.to_node, link.to_socket)
    curve = context.preferences.themes[0].node_editor.noodle_curving
    dx, dy = abs(b[0]-a[0]), abs(b[1]-a[1])
    offset = curve*.1*dx*min(1,dy/dx*(4.5-.25*curve)) if dx else 0
    if not curve:
        return [a, tuple(a[k]+(b[k]-a[k])/3 for k in (0,1)), tuple(a[k]+2*(b[k]-a[k])/3 for k in (0,1)), b]
    return [a,(a[0]+offset,a[1]),(b[0]-offset,b[1]),b]


def color(link, context):
    try:
        return tuple(link.from_socket.draw_color(context, link.from_node))
    except (AttributeError, TypeError):
        return (.65,.65,.65,1)


def to_view(context, point):
    scale = context.preferences.system.ui_scale
    return tuple(v / scale for v in window_region(context).view2d.region_to_view(*point))


def window_region(context):
    return next(r for r in context.area.regions if r.type == 'WINDOW')


def to_region(context, point):
    scale = context.preferences.system.ui_scale
    return window_region(context).view2d.view_to_region(point[0]*scale,point[1]*scale,clip=False)
