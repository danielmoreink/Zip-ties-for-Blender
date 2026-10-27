"""Node Zip Ties: native reroute bundles for unmodified Blender."""
import bpy
from bpy.app.handlers import persistent
from . import preferences, interaction, rendering, selection, ui, clipboard, data, routing

classes = [preferences.NZT_Preferences] + interaction.classes + clipboard.classes + ui.classes


@persistent
def reset_runtime(*_):
    selection.clear()
    clipboard.payload = None


def migrate_routes():
    """Upgrade old overlay-only ties once, outside any drawing callback."""
    trees = list(bpy.data.node_groups)
    trees += [m.node_tree for m in bpy.data.materials if m.node_tree]
    trees += [w.node_tree for w in bpy.data.worlds if w.node_tree]
    for tree in trees:
        if tree.is_editable and data.KEY in tree:
            ties = data.read(tree)
            needed = {(t['id'],k) for t in ties for k in t['members']}
            existing = {(n.get(routing.TIE),n.get(routing.OWNER)) for n in tree.nodes if routing.managed(n)}
            if needed - existing or (needed and tree.get(routing.LAYOUT_KEY) != routing.LAYOUT_VERSION):
                data.write(tree,ties)
    return None


@persistent
def load_routes(*_):
    migrate_routes()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_context_menu.append(ui.context_menu)
    interaction.add_keymaps()
    rendering.register()
    bpy.app.handlers.load_post.append(load_routes)
    bpy.app.timers.register(migrate_routes,first_interval=.1)
    for handlers in [bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post]:
        handlers.append(reset_runtime)


def unregister():
    if bpy.app.timers.is_registered(migrate_routes):
        bpy.app.timers.unregister(migrate_routes)
    if load_routes in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_routes)
    rendering.unregister()
    interaction.remove_keymaps()
    bpy.types.NODE_MT_context_menu.remove(ui.context_menu)
    for handlers in [bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post]:
        if reset_runtime in handlers:
            handlers.remove(reset_runtime)
    selection.clear()
    clipboard.payload = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
