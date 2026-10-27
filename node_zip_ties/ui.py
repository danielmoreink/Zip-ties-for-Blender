import math
import bpy
from . import data, rendering, selection
from .preferences import prefs


def state(context):
    tree = rendering.tree_of(context)
    chosen = selection.of(tree) if tree else set()
    return tree, [t for t in data.read(tree) if t['id'] in chosen] if tree else []


def selected_actions(layout,context):
    tree,chosen = state(context)
    col = layout.column(align=True)
    col.enabled = bool(tree and tree.is_editable and chosen)
    col.operator('node.zip_tie_color',text='Color…')
    col.operator('node.zip_tie_edit',text='Remove Tie' if len(chosen)==1 else 'Remove Ties',icon='X').action = 'DELETE'


class NZT_MT_context(bpy.types.Menu):
    bl_label = 'Zip Tie'

    def draw(self,context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator('node.zip_tie_gesture',text='Tie Wires',icon='LINKED')
        layout.separator()
        tree,chosen = state(context)
        col = layout.column()
        col.enabled = bool(tree and tree.is_editable and chosen)
        col.operator('node.zip_tie_rotate',text='Rotate Freely (R)')
        for angle,label in [(math.pi/4,'Rotate +45°'),(math.pi/2,'Rotate +90°')]:
            op = col.operator('node.zip_tie_edit',text=label)
            op.action = 'ROTATE'
            op.angle = angle
        selected_actions(layout,context)


class NZT_PT_panel(bpy.types.Panel):
    bl_label = 'Node Zip Ties'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Zip Ties'

    def draw(self,context):
        layout = self.layout
        options = prefs(context)
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.label(text=f'{options.gesture_key} + drag across wires',icon='INFO')
        tree,chosen = state(context)
        if not tree:
            layout.label(text='Open a node tree to start.')
        elif not tree.is_editable:
            layout.label(text='This node tree is read-only.',icon='LOCKED')
        layout.separator()
        layout.label(text=f'Selected Ties · {len(chosen)}')
        selected_actions(layout,context)
        if rendering.last_error:
            layout.label(text=rendering.last_error,icon='ERROR')


class ChildPanel:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Zip Ties'
    bl_parent_id = 'NZT_PT_panel'
    bl_options = {'DEFAULT_CLOSED'}


class NZT_PT_appearance(ChildPanel,bpy.types.Panel):
    bl_label = 'Appearance — All Ties'

    def draw(self,context):
        layout = self.layout
        options = prefs(context)
        layout.prop(options,'enabled',text='Show Straps')
        layout.label(text='Global settings · all node trees')
        for name,label in [('spacing','Strand Spacing'),('width','Strap Width')]:
            layout.label(text=label)
            layout.prop(options,name,text='')
        layout.separator()
        layout.label(text='New Tie Color')
        layout.prop(options,'color_mode',text='')


class NZT_PT_maintenance(ChildPanel,bpy.types.Panel):
    bl_label = 'Maintenance'

    def draw(self,context):
        layout = self.layout
        tree,chosen = state(context)
        layout.enabled = bool(tree and tree.is_editable and data.read(tree))
        layout.operator('node.zip_tie_edit',text='Remove Missing Wire References').action = 'PRUNE'


def context_menu(self,context):
    if rendering.tree_of(context):
        self.layout.separator()
        self.layout.menu('NZT_MT_context',text='Zip Ties')


classes = [NZT_MT_context,NZT_PT_panel,NZT_PT_appearance,NZT_PT_maintenance]
