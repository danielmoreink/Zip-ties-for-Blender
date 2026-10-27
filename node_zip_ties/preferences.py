import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty


def prefs(context):
    entry = context.preferences.addons.get(__package__)
    return entry.preferences if entry else DEFAULTS


class Defaults:
    enabled = True
    spacing = 8.0
    width = 8.0
    color_mode = 'RANDOM'
    gesture_key = 'Z'


DEFAULTS = Defaults()


def update_key(self, context):
    from . import interaction
    interaction.remove_keymaps()
    interaction.add_keymaps()


def update_visibility(self,context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()


def update_routes(self,context):
    from . import data, routing
    trees = list(bpy.data.node_groups)
    trees += [m.node_tree for m in bpy.data.materials if m.node_tree]
    trees += [w.node_tree for w in bpy.data.worlds if w.node_tree]
    for tree in trees:
        if tree.is_editable and data.KEY in tree:
            routing.sync(tree,data.read(tree),self.spacing,self.width)
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()


class NZT_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    enabled: BoolProperty(name='Show Straps', default=True,update=update_visibility,
        description='Show colored straps; native routed wires and editing remain available')
    spacing: FloatProperty(name='Strand spacing', default=8, min=4, max=30,update=update_routes)
    width: FloatProperty(name='Strap width', default=8, min=2, max=20,update=update_routes)
    color_mode: EnumProperty(name='New tie color', items=[('RANDOM','Random',''),('GREY','Grey',''),('WIRES','Match wires','')])
    gesture_key: EnumProperty(name='Hold key', default='Z', update=update_key,
        items=[(k,k,'Hold then drag; bare key starts a modal gesture') for k in ['Z','X','C','T','Y']])

    def draw(self, context):
        layout = self.layout
        for name in ['enabled','gesture_key','color_mode','spacing','width']:
            layout.prop(self, name)
