"""Explicit clipboard commands preserve ties in the same undo operation as nodes.

Uses Blender's clipboard for nodes. Tie metadata is session-local, and only applied
when pasted UUIDs match the corresponding copy. Ordinary Ctrl-C/V are untouched.
"""
import copy
import json
import uuid
import bpy
from . import data, rendering, selection, routing

payload = None


class NZT_OT_copy(bpy.types.Operator):
    bl_idname = 'node.zip_tie_copy'
    bl_label = 'Copy Nodes with Ties'
    bl_description = 'Copy selected nodes and their associated tie routes; use Paste here to restore the ties'

    @classmethod
    def poll(cls,context):
        tree = rendering.tree_of(context)
        return bool(tree and tree.is_editable and any(n.select and not routing.managed(n) for n in tree.nodes))

    def execute(self,context):
        global payload
        tree = rendering.tree_of(context)
        if not tree.is_editable:
            return {'CANCELLED'}
        data.repair_duplicate_ids(tree)
        chosen = {data.uid(n):tuple(n.location_absolute) for n in tree.nodes if n.select and not routing.managed(n)}
        ties = []
        for tie in data.read(tree):
            if all(json.loads(k)[0] in chosen and json.loads(k)[2] in chosen for k in tie['members']):
                ties.append(tie)
        original_selection = [(n,n.select) for n in tree.nodes]
        try:
            for n in tree.nodes:
                if routing.managed(n):
                    src,_,dst,_ = json.loads(n[routing.OWNER])
                    n.select = src in chosen and dst in chosen
            result = bpy.ops.node.clipboard_copy()
        finally:
            for node,selected in original_selection:
                node.select = selected
        if result == {'FINISHED'}:
            payload = dict(nodes=chosen,ties=copy.deepcopy(ties))
        return result


class NZT_OT_paste(bpy.types.Operator):
    bl_idname = 'node.zip_tie_paste'
    bl_label = 'Paste Nodes with Ties'
    bl_options = {'UNDO'}
    bl_description = 'Paste the nodes copied with this add-on, including their associated ties'

    @classmethod
    def poll(cls,context):
        tree = rendering.tree_of(context)
        return bool(tree and tree.is_editable and payload)

    def execute(self,context):
        tree = rendering.tree_of(context)
        before = {n.as_pointer() for n in tree.nodes}
        result = bpy.ops.node.clipboard_paste()
        if result != {'FINISHED'}:
            return result
        pasted = [n for n in tree.nodes if n.as_pointer() not in before]
        mapping = {}
        offsets = []
        for n in pasted:
            old = data.uid(n)
            new = uuid.uuid4().hex
            n[data.NODE_ID] = new
            if payload and old in payload['nodes']:
                mapping[old] = new
                offsets.append(tuple(n.location_absolute[k]-payload['nodes'][old][k] for k in (0,1)))
        if not payload or not offsets:
            return result
        delta = offsets[0]
        if any(any(abs(o[k]-delta[k])>.01 for k in (0,1)) for o in offsets):
            return result
        tie_ids = {t['id']:uuid.uuid4().hex for t in payload['ties']}
        for node in pasted:
            if not routing.managed(node):
                continue
            src,out,dst,inp = json.loads(node[routing.OWNER])
            if src in mapping and dst in mapping and node.get(routing.TIE) in tie_ids:
                node[routing.OWNER] = json.dumps([mapping[src],out,mapping[dst],inp],separators=(',',':'))
                node[routing.TIE] = tie_ids[node[routing.TIE]]
            else:
                for attr in (routing.OWNER,routing.TIE,routing.SLOT):
                    if attr in node:
                        del node[attr]
        ties = data.read(tree)
        live = routing.live_keys(tree)
        selected = selection.of(tree)
        selected.clear()
        for original in payload['ties']:
            tie = copy.deepcopy(original)
            keys = []
            for key in tie['members']:
                src,out,dst,inp = json.loads(key)
                if src not in mapping or dst not in mapping:
                    break
                keys.append(json.dumps([mapping[src],out,mapping[dst],inp],separators=(',',':')))
            if len(keys) == len(tie['members']) and set(keys) <= live:
                tie['members'] = keys
                tie['id'] = tie_ids[original['id']]
                tie['pos'] = [tie['pos'][k]+delta[k] for k in (0,1)]
                ties.append(tie)
                selected.add(tie['id'])
        data.write(tree,ties)
        return result


classes = [NZT_OT_copy,NZT_OT_paste]
