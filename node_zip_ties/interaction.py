import copy
import json
import math
import random
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty
from . import data, geometry as g, rendering, selection, sockets, routing, transforms
from .preferences import prefs

keymaps = []


def redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()


def point(context,event):
    region = sockets.window_region(context)
    return sockets.to_view(context,(event.mouse_x-region.x,event.mouse_y-region.y))


def hit_at(context,p):
    tree = rendering.tree_of(context)
    options = prefs(context)
    if not options.enabled:
        return None  # Hidden straps must not intercept ordinary canvas clicks.
    # Screen-pixel tolerance remains constant during navigation.
    a = sockets.to_view(context,(0,0))
    b = sockets.to_view(context,(6,0))
    return next((t for t in reversed(rendering.shown(tree,data.read(tree)))
                 if g.marker_hit(t,p,options.spacing,options.width,abs(b[0]-a[0]))),None)


def stroke_targets(context,ties,a,b):
    tree = rendering.tree_of(context)
    options = prefs(context)
    cuts = {t['id'] for t in rendering.shown(tree,ties) if g.marker_cut(t,a,b,options.spacing,options.width)}
    hits = []
    if not cuts:
        for link in tree.links:
            if link.is_hidden:
                continue
            key = data.link_key(link)
            hit = g.curve_hit(a,b,[sockets.controls(link,context)])
            if hit:
                hits.append((key,hit,link))
    # Several physical segments may belong to one logical wire.
    unique = {}
    for entry in hits:
        if entry[0] not in unique or entry[1][0] < unique[entry[0]][1][0]:
            unique[entry[0]] = entry
    return list(unique.values()),cuts


def new_color(context,links):
    mode = prefs(context).color_mode
    if mode == 'GREY':
        return (.55,.55,.58,1)
    if mode == 'WIRES':
        colors = [sockets.color(l,context) for l in links]
        return max(colors,key=colors.count)
    return random.choice([(.9,.28,.3,1),(.25,.4,.86,1),(.27,.65,.35,1),(.99,.77,.24,1),(.56,.3,.78,1)])


class NodeOperator:
    @classmethod
    def poll(cls,context):
        tree = rendering.tree_of(context)
        return tree is not None and tree.is_editable


class NZT_OT_hover(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_hover'
    bl_label = 'Zip Tie Hover'
    bl_options = {'INTERNAL'}

    def invoke(self,context,event):
        tie = hit_at(context,point(context,event))
        key = context.area.as_pointer()
        value = tie['id'] if tie else None
        if selection.hovered.get(key) != value:
            selection.hovered[key] = value
            redraw(context)
        return {'PASS_THROUGH'}


class NZT_OT_gesture(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_gesture'
    bl_label = 'Tie Wires'
    bl_description = 'Drag a line across at least two wires; crossing a tie cuts it'
    bl_options = {'REGISTER','UNDO','BLOCKING'}

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.node_ids = [(n,n.get(data.NODE_ID)) for n in self.tree.nodes]
        # Assign IDs before collecting keys, within this operator's undo step.
        data.repair_duplicate_ids(self.tree)
        self.ties = data.prune(self.tree,data.read(self.tree))
        self.start = point(context,event) if event.type == 'LEFTMOUSE' else None
        self.area_key = context.area.as_pointer()
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set('Zip ties: drag across wires • Esc cancels')
        return {'RUNNING_MODAL'}

    def finish(self,context,cancel=False):
        if cancel:
            for node,original in self.node_ids:
                if original is None:
                    if data.NODE_ID in node:
                        del node[data.NODE_ID]
                else:
                    node[data.NODE_ID] = original
        selection.preview.pop(self.area_key,None)
        context.workspace.status_text_set(None)
        redraw(context)
        return {'CANCELLED'} if cancel else {'FINISHED'}

    def modal(self,context,event):
        if event.type in {'ESC','RIGHTMOUSE'} and event.value == 'PRESS':
            return self.finish(context,True)
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.start = point(context,event)
        if self.start is not None and event.type == 'MOUSEMOVE':
            p = point(context,event)
            _,cuts = stroke_targets(context,self.ties,self.start,p)
            selection.preview[self.area_key] = (self.start,p,cuts)
            redraw(context)
        if self.start is not None and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            p = point(context,event)
            hits,cuts = stroke_targets(context,self.ties,self.start,p)
            if cuts:
                self.ties = [t for t in self.ties if t['id'] not in cuts]
                selection.of(self.tree).difference_update(cuts)
            elif len(hits) >= 2:
                tangents = [h[1][1] for h in hits]
                angle = math.atan2(sum(v[1] for v in tangents),sum(v[0] for v in tangents))
                _,normal = g.axes(angle)
                position = lambda h: g.add(self.start,g.mul(g.sub(p,self.start),h[1][0]))
                pos = [sum(position(h)[k] for h in hits)/len(hits) for k in (0,1)]
                hits.sort(key=lambda h:g.dot(position(h),normal))
                tie = data.new_tie(pos,angle,[h[0] for h in hits],self.ties,new_color(context,[h[2] for h in hits]))
                self.ties.append(tie)
                selection.of(self.tree).clear()
                selection.of(self.tree).add(tie['id'])
            else:
                return self.finish(context,True)
            data.write(self.tree,self.ties)
            return self.finish(context)
        return {'RUNNING_MODAL'}


class NZT_OT_pick(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_pick'
    bl_label = 'Select or Transform Zip Tie'
    bl_options = {'UNDO','BLOCKING'}

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.start = point(context,event)
        hit = hit_at(context,self.start)
        if not hit:
            if not event.shift and not event.ctrl:
                selection.of(self.tree).clear()
                redraw(context)
            return {'PASS_THROUGH'}
        selected = selection.of(self.tree)
        if event.type == 'RIGHTMOUSE':
            if hit['id'] not in selected:
                selected.clear()
                selected.add(hit['id'])
            bpy.ops.wm.call_menu(name='NZT_MT_context')
            return {'FINISHED'}
        if event.value == 'DOUBLE_CLICK':
            data.write(self.tree,[t for t in data.read(self.tree) if t['id'] != hit['id']])
            selected.discard(hit['id'])
            redraw(context)
            return {'FINISHED'}
        if event.ctrl:
            selected.symmetric_difference_update({hit['id']})
            redraw(context)
            return {'FINISHED'}
        if not event.shift and hit['id'] not in selected:
            selected.clear()
        selected.add(hit['id'])
        self.original = data.read(self.tree)
        self.hit = hit
        self.rotate = event.shift
        self.offset = hit['angle'] - math.atan2(self.start[1]-hit['pos'][1],self.start[0]-hit['pos'][0])
        context.window_manager.modal_handler_add(self)
        redraw(context)
        return {'RUNNING_MODAL'}

    def modal(self,context,event):
        if event.type in {'ESC','RIGHTMOUSE'} and event.value == 'PRESS':
            data.write(self.tree,self.original)
            redraw(context)
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            p = point(context,event)
            delta = g.sub(p,self.start)
            ties = copy.deepcopy(self.original)
            angle = math.atan2(p[1]-self.hit['pos'][1],p[0]-self.hit['pos'][0])+self.offset
            if not event.alt:
                angle = round(angle/(math.pi/12))*(math.pi/12)
            for t in ties:
                if t['id'] in selection.of(self.tree):
                    if self.rotate:
                        t['angle'] += angle-self.hit['angle']
                    else:
                        t['pos'] = list(g.add(t['pos'],delta))
            data.write(self.tree,ties)
            redraw(context)
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class NZT_OT_move(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_move'
    bl_label = 'Move Zip Ties'
    bl_description = 'G moves selected ties; press G again to slide between neighbouring ties'
    bl_options = {'UNDO','BLOCKING'}

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.original = data.read(self.tree)
        chosen = selection.of(self.tree)
        self.ids = {t['id'] for t in self.original if t['id'] in chosen}
        self.start = point(context,event)
        if not self.ids:
            hit = hit_at(context,self.start)
            if not hit:
                return {'PASS_THROUGH'}
            chosen.clear()
            chosen.add(hit['id'])
            self.ids = {hit['id']}
        self.guides = {t['id']:transforms.slide_guide(self.tree,t,context)
                       for t in self.original if t['id'] in self.ids}
        self.cursor = self.start
        self.slide = False
        context.window_manager.modal_handler_add(self)
        self.status(context)
        return {'RUNNING_MODAL'}

    def status(self,context):
        text = 'Slide ties between neighbours' if self.slide else 'Move ties • G again to slide'
        context.workspace.status_text_set(text+' • Click/Enter confirm • Esc/right-click cancel')

    def update(self,context):
        delta = g.sub(self.cursor,self.start)
        ties = copy.deepcopy(self.original)
        for tie in ties:
            if tie['id'] in self.ids:
                position = g.add(tie['pos'],delta)
                tie['pos'] = list(transforms.project(self.guides[tie['id']],position) if self.slide else position)
        data.write(self.tree,ties)
        redraw(context)

    def finish(self,context,cancel=False):
        if cancel:
            data.write(self.tree,self.original)
        context.workspace.status_text_set(None)
        redraw(context)
        return {'CANCELLED'} if cancel else {'FINISHED'}

    def modal(self,context,event):
        if event.value == 'PRESS':
            if event.type in {'ESC','RIGHTMOUSE'}:
                return self.finish(context,True)
            if event.type in {'LEFTMOUSE','RET','NUMPAD_ENTER'}:
                return self.finish(context)
            if event.type == 'G' and not getattr(event,'is_repeat',False) and not self.slide:
                self.slide = True
                self.status(context)
                self.update(context)
        if event.type == 'MOUSEMOVE':
            self.cursor = point(context,event)
            self.update(context)
        return {'RUNNING_MODAL'}


class NZT_OT_scale(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_scale'
    bl_label = 'Scale Zip Ties'
    bl_description = 'Scale selected tie lengths and noodle gaps; click/Enter confirms, Esc cancels'
    bl_options = {'UNDO','BLOCKING'}

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.original = data.read(self.tree)
        chosen = selection.of(self.tree)
        self.ids = {t['id'] for t in self.original if t['id'] in chosen}
        self.start = point(context,event)
        if not self.ids:
            hit = hit_at(context,self.start)
            if not hit:
                return {'PASS_THROUGH'}
            chosen.clear()
            chosen.add(hit['id'])
            self.ids = {hit['id']}
        ties = [t for t in self.original if t['id'] in self.ids]
        self.pivot = tuple(sum(t['pos'][k] for t in ties)/len(ties) for k in (0,1))
        self.radius = math.hypot(*g.sub(self.start,self.pivot))
        if self.radius < 1:
            # At the exact centre, use a virtual reference so left/right motion
            # can still shrink/grow instead of dividing by zero or jumping.
            self.radius = max(32,max(g.half_length(t,prefs(context).spacing) for t in ties))
            self.pivot = (self.start[0]-self.radius,self.start[1])
        self.factor = 1.0
        self.numeric = ''
        context.window_manager.modal_handler_add(self)
        self.status(context)
        return {'RUNNING_MODAL'}

    def status(self,context):
        context.workspace.status_text_set(f'Scale ties: {self.numeric or format(self.factor,".3f")} × • Type a factor • Click/Enter confirm • Esc/right-click cancel')

    def update(self,context):
        ties = copy.deepcopy(self.original)
        for tie in ties:
            if tie['id'] in self.ids:
                tie['scale'] = max(.1,min(20,tie.get('scale',1.0)*self.factor))
        data.write(self.tree,ties)
        self.status(context)
        redraw(context)

    def finish(self,context,cancel=False):
        if cancel:
            data.write(self.tree,self.original)
        context.workspace.status_text_set(None)
        redraw(context)
        return {'CANCELLED'} if cancel else {'FINISHED'}

    def modal(self,context,event):
        if event.value == 'PRESS':
            if event.type in {'ESC','RIGHTMOUSE'}:
                return self.finish(context,True)
            if event.type in {'LEFTMOUSE','RET','NUMPAD_ENTER'}:
                return self.finish(context)
            digits = dict(zip(['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE'],'0123456789'))
            digits.update({f'NUMPAD_{i}':str(i) for i in range(10)})
            if event.type in digits and len(self.numeric)<16:
                self.numeric += digits[event.type]
            elif event.type in {'PERIOD','NUMPAD_PERIOD'} and '.' not in self.numeric:
                self.numeric += '.'
            elif event.type == 'BACK_SPACE':
                self.numeric = self.numeric[:-1]
            else:
                return {'RUNNING_MODAL'}
            try:
                self.factor = max(.01,min(200,float(self.numeric))) if self.numeric else 1.0
            except ValueError:
                self.factor = 1.0
            self.update(context)
        if event.type == 'MOUSEMOVE' and not self.numeric:
            self.factor = max(.01,min(200,math.hypot(*g.sub(point(context,event),self.pivot))/self.radius))
            self.update(context)
        return {'RUNNING_MODAL'}


class NZT_OT_rotate(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_rotate'
    bl_label = 'Rotate Zip Ties Freely'
    bl_description = 'Rotate selected ties with the mouse; click or Enter confirms, Esc cancels'
    bl_options = {'UNDO','BLOCKING'}

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.original = data.read(self.tree)
        chosen = selection.of(self.tree)
        self.ids = {t['id'] for t in self.original if t['id'] in chosen}
        if not self.ids:
            hit = hit_at(context,point(context,event))
            if not hit:
                return {'PASS_THROUGH'}
            chosen.clear()
            chosen.add(hit['id'])
            self.ids = {hit['id']}
        ties = [t for t in self.original if t['id'] in self.ids]
        self.pivot = tuple(sum(t['pos'][k] for t in ties)/len(ties) for k in (0,1))
        self.previous = None
        self.delta = 0.0
        self.track(point(context,event))
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set('Rotate zip ties freely • Click/Enter confirm • Esc/right-click cancel')
        return {'RUNNING_MODAL'}

    def track(self,p):
        x,y = g.sub(p,self.pivot)
        if math.hypot(x,y) < 1e-4:
            return
        angle = math.atan2(y,x)
        if self.previous is not None:
            # Unwrap at +/-pi, supporting continuous turns without a jump.
            change = angle-self.previous
            self.delta += math.atan2(math.sin(change),math.cos(change))
        self.previous = angle

    def finish(self,context,cancel=False):
        if cancel:
            data.write(self.tree,self.original)
        context.workspace.status_text_set(None)
        redraw(context)
        return {'CANCELLED'} if cancel else {'FINISHED'}

    def modal(self,context,event):
        if event.value == 'PRESS':
            if event.type in {'ESC','RIGHTMOUSE'}:
                return self.finish(context,True)
            if event.type in {'LEFTMOUSE','RET','NUMPAD_ENTER'}:
                return self.finish(context)
        if event.type == 'MOUSEMOVE':
            self.track(point(context,event))
            ties = copy.deepcopy(self.original)
            for tie in ties:
                if tie['id'] in self.ids:
                    tie['angle'] += self.delta
            data.write(self.tree,ties)
            redraw(context)
        return {'RUNNING_MODAL'}


class NZT_OT_color(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_color'
    bl_label = 'Tie Color'
    bl_description = 'Change the color of the selected ties'
    bl_options = {'REGISTER','UNDO'}
    color: FloatVectorProperty(name='Color',subtype='COLOR',size=4,min=0,max=1,default=(.55,.55,.58,1))

    @classmethod
    def poll(cls,context):
        tree = rendering.tree_of(context)
        return bool(tree and tree.is_editable and any(t['id'] in selection.of(tree) for t in data.read(tree)))

    def invoke(self,context,event):
        tree = rendering.tree_of(context)
        self.color = next(t['color'] for t in data.read(tree) if t['id'] in selection.of(tree))
        return context.window_manager.invoke_props_dialog(self)

    def draw(self,context):
        self.layout.template_color_picker(self,'color',value_slider=True)
        self.layout.prop(self,'color',text='')

    def execute(self,context):
        tree = rendering.tree_of(context)
        ties = data.read(tree)
        for tie in ties:
            if tie['id'] in selection.of(tree):
                tie['color'] = list(self.color)
        data.write(tree,ties)
        redraw(context)
        return {'FINISHED'}


class NZT_OT_edit(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_edit'
    bl_label = 'Edit Selected Zip Ties'
    bl_options = {'REGISTER','UNDO'}
    action: EnumProperty(items=[('DELETE','Remove',''),('ROTATE','Rotate',''),
        ('PRUNE','Remove Missing Wire References','Remove missing connections from ties; does not delete disconnected nodes')],options={'HIDDEN'})
    angle: FloatProperty(default=math.pi/2)
    delete_nodes: BoolProperty(default=False,options={'HIDDEN'})

    def execute(self,context):
        tree = rendering.tree_of(context)
        selected = selection.of(tree)
        if not selected and self.action != 'PRUNE':
            return {'PASS_THROUGH'}
        ties = data.read(tree)
        if self.action == 'DELETE':
            ties = [t for t in ties if t['id'] not in selected]
            selected.clear()
            if self.delete_nodes:
                # Restore logical connections and remove owned helpers before
                # deleting their endpoints, within the same undo step.
                data.write(tree,ties)
                for node in list(tree.nodes):
                    if node.select:
                        tree.nodes.remove(node)
                ties = data.prune(tree,ties)
        elif self.action == 'PRUNE':
            ties = data.prune(tree,ties)
        else:
            for t in ties:
                if t['id'] in selected:
                    t['angle'] += self.angle
        data.write(tree,ties)
        redraw(context)
        return {'FINISHED'}


class NZT_OT_box(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_box'
    bl_label = 'Box Select Ties and Nodes'
    bl_options = {'UNDO','BLOCKING'}
    bl_description = 'Drag a box to select nodes and ties together; Shift adds to selection'

    def invoke(self,context,event):
        self.start = None
        self.extend = event.shift
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self,context,event):
        if event.type in {'ESC','RIGHTMOUSE'}:
            selection.boxes.pop(context.area.as_pointer(),None)
            redraw(context)
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.start = point(context,event)
        if self.start and event.type == 'MOUSEMOVE':
            p = point(context,event)
            selection.boxes[context.area.as_pointer()] = (self.start,p)
            redraw(context)
        if self.start and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            tree = rendering.tree_of(context)
            p = point(context,event)
            lo = [min(self.start[k],p[k]) for k in (0,1)]
            hi = [max(self.start[k],p[k]) for k in (0,1)]
            inside = lambda v: all(lo[k]<=v[k]<=hi[k] for k in (0,1))
            chosen = selection.of(tree)
            if not self.extend:
                chosen.clear()
            options = prefs(context)
            corners = [tuple(lo),(hi[0],lo[1]),tuple(hi),(lo[0],hi[1])]
            def tie_overlaps(tie):
                polygons = g.marker(tie,options.spacing,options.width)
                return (any(inside(p) for poly in polygons for p in poly) or
                        any(g.marker_hit(tie,p,options.spacing,options.width) for p in corners) or
                        any(g.marker_cut(tie,a,b,options.spacing,options.width)
                            for a,b in zip(corners,corners[1:]+corners[:1])))
            chosen.update(t['id'] for t in data.read(tree) if tie_overlaps(t))
            for n in tree.nodes:
                if not self.extend:
                    n.select = False
                scale = context.preferences.system.ui_scale
                p = n.location_absolute
                width,height = n.dimensions.x/scale,n.dimensions.y/scale
                overlaps = p.x <= hi[0] and p.x+width >= lo[0] and p.y >= lo[1] and p.y-height <= hi[1]
                if not routing.managed(n) and overlaps:
                    n.select = True
            redraw(context)
            selection.boxes.pop(context.area.as_pointer(),None)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class NZT_OT_move_nodes(NodeOperator,bpy.types.Operator):
    bl_idname = 'node.zip_tie_move_selection'
    bl_label = 'Move Selected Nodes and Ties'
    bl_options = {'UNDO','BLOCKING'}
    bl_description = 'Move selected nodes and ties together; click/Enter confirms, Esc cancels'

    @classmethod
    def poll(cls,context):
        tree = rendering.tree_of(context)
        return bool(tree and tree.is_editable and (
            any(n.select and not routing.managed(n) for n in tree.nodes) or
            any(t['id'] in selection.of(tree) for t in data.read(tree))))

    def invoke(self,context,event):
        self.tree = rendering.tree_of(context)
        self.nodes = [(n,tuple(n.location)) for n in self.tree.nodes if n.select and not routing.managed(n)]
        self.ties = data.read(self.tree)
        self.start = point(context,event)
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set('Move nodes and ties • Click/Enter confirm • Esc/right-click cancel')
        return {'RUNNING_MODAL'}

    def modal(self,context,event):
        cancel = event.type in {'ESC','RIGHTMOUSE'} and event.value == 'PRESS'
        if cancel or event.type == 'MOUSEMOVE':
            d = (0,0) if cancel else g.sub(point(context,event),self.start)
            for n,pos in self.nodes:
                # Children of selected frames already inherit their parent's movement.
                parent = n.parent
                ancestors_selected = False
                while parent:
                    ancestors_selected |= parent.select
                    parent = parent.parent
                if not ancestors_selected:
                    n.location = g.add(pos,d)
            selected_nodes = {data.uid(n) for n,_ in self.nodes}
            ties = copy.deepcopy(self.ties)
            for t in ties:
                endpoints = {v for key in t['members'] for v in (json.loads(key)[0],json.loads(key)[2])}
                if t['id'] in selection.of(self.tree) or endpoints <= selected_nodes:
                    t['pos'] = list(g.add(t['pos'],d))
            data.write(self.tree,ties)
            redraw(context)
        if cancel:
            context.workspace.status_text_set(None)
            return {'CANCELLED'}
        if event.type in {'LEFTMOUSE','RET'} and event.value == 'PRESS':
            context.workspace.status_text_set(None)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


def add_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name='Node Editor',space_type='NODE_EDITOR')
    # key_modifier preserves the bare Blender key command. Menu command also works without key.
    key = prefs(bpy.context).gesture_key
    entries = [('node.zip_tie_gesture','LEFTMOUSE','PRESS',dict(key_modifier=key)),
               ('node.zip_tie_pick','LEFTMOUSE','PRESS',dict(any=True)),
               ('node.zip_tie_pick','LEFTMOUSE','DOUBLE_CLICK',dict(any=True)),
               ('node.zip_tie_pick','RIGHTMOUSE','PRESS',dict(any=True))]
    for op,kind,value,kw in entries:
        item = km.keymap_items.new(op,kind,value,**kw)
        keymaps.append((km,item))
    keymaps.append((km,km.keymap_items.new('node.zip_tie_hover','MOUSEMOVE','ANY',any=True)))
    keymaps.append((km,km.keymap_items.new('node.zip_tie_rotate','R','PRESS')))
    keymaps.append((km,km.keymap_items.new('node.zip_tie_move','G','PRESS')))
    keymaps.append((km,km.keymap_items.new('node.zip_tie_scale','S','PRESS')))
    item = km.keymap_items.new('node.zip_tie_edit','X','PRESS')
    item.properties.action = 'DELETE'
    item.properties.delete_nodes = False
    keymaps.append((km,item))
    for key in ['DEL','BACK_SPACE']:
        item = km.keymap_items.new('node.zip_tie_edit',key,'PRESS')
        item.properties.action = 'DELETE'
        item.properties.delete_nodes = True
        keymaps.append((km,item))


def remove_keymaps():
    for km,item in keymaps:
        km.keymap_items.remove(item)
    keymaps.clear()


classes = [NZT_OT_hover,NZT_OT_gesture,NZT_OT_pick,NZT_OT_move,NZT_OT_scale,NZT_OT_rotate,NZT_OT_color,NZT_OT_edit,NZT_OT_box,NZT_OT_move_nodes]
