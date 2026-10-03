# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_island_tools

import sys
import time
import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "Island Tools",
    "description": "Toolset for working with mesh islands",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 3, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Tool panel > 1D > Island Tools",
    "doc_url": "https://github.com/Korchy/1d_island_tools",
    "tracker_url": "https://github.com/Korchy/1d_island_tools",
    "category": "All"
}


# MAIN CLASS

class IslandTools:

    @staticmethod
    def islands(obj):
        # get islands for object
        #   list of islands. Each island - one separated part of the mesh
        #   islands = [{'vertices': [GMVert, ...], 'edges': [BMEdge, ...], 'faces': [BMFace, ...]}, ...]
        islands = []
        start_time = time.time()
        # current mode
        mode = obj.mode
        # switch to OBJECT mode
        if obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # create BMesh object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        # bm.verts.ensure_lookup_table()
        # create islands db from BMesh object
        checked = set() # already checked vertices
        # check all vertices of the mesh
        for vert in bm.verts:
            if vert in checked:
                continue
            checked.add(vert)
            # current island
            vertices = []
            edges = set()
            faces = set()
            # processing vertices
            checking_vertices = [vert]
            while checking_vertices:
                current_vert = checking_vertices.pop()
                vertices.append(current_vert)
                # check vertices connected with current by edges
                for edge in current_vert.link_edges:
                    edges.add(edge)
                    other = edge.other_vert(current_vert)
                    if other not in checked:
                        checked.add(other)
                        checking_vertices.append(other)
                    for face in edge.link_faces:
                        faces.add(face)
            # append new island to the islands db
            islands.append(
                {
                    'vertices': vertices,
                    'edges': edges,
                    'faces': faces
                }
            )
        print('Islands DB created in : ' + str(time.time() - start_time) \
              + ' sec, got ' + str(len(islands)) + ' islands.')
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        return islands, bm

    @classmethod
    def dec_select(cls, context):
        # Decrease selection to whole selected islands
        src_obj = context.active_object
        start_time = time.time()
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # get islands db
        db, bm = cls.islands(obj=src_obj)
        # remove selection from partially selected islands
        for island in db:
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                for vertex in island['vertices']:
                    vertex.select = False
                for edge in island['edges']:
                    edge.select = False
                for face in island['faces']:
                    face.select = False
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Dec Select executed in : ' + str(time.time() - start_time) + ' sec.')

    @classmethod
    def select_islands_by(cls, context, op, op_mode='OR', compare_mode='EQ',
                          mode_verts=False, threshold_verts=5.0,
                          mode_edges=False, threshold_edges=5.0,
                          mode_area=False, threshold_area=5.0):
        # select islands by mode (Verts amount / Summary length of edges / Summary area of faces)
        #   threshold - %
        #   op_mode -   OR - select if meets any of conditions (by verts/edges/faces)
        #               AND - select if meets all of conditions (by verts/edges/faces)
        #   compare_mode -  EQ (=) - equal with threshold
        #                   LE (<=) - less than or equal with threshold
        #                   GE (>=) - grater than
        src_obj = context.active_object
        start_time = time.time()
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # get islands db
        db, bm = cls.islands(obj=src_obj)
        # select islands
        vertices_amounts = set()
        edges_length = set()
        faces_areas = set()
        selected_islands = []   # selected islands indices in db
        # collect amount of vertices for fully selected islands
        for _i, island in enumerate(db):
            # for fully selected islands
            if all(vertex.select for vertex in island['vertices']):
                selected_islands.append(_i)
                # collect vertices amount
                vertices_amounts.add(len(island['vertices']))
                # collect summary edges lengths
                edges_length.add(sum([_edge.calc_length() for _edge in island['edges']]))
                # collect summary faces area
                faces_areas.add(sum([_face.calc_area() for _face in island['faces']]))
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                cls._deselect_island(island=island)
        # select islands with close amount of vertices
        for island in db:
            # verts threshold
            if compare_mode == 'LE':
                min_amount = len(island['vertices']) * (1 - threshold_verts / 100)
                max_amount = sys.maxsize
            elif compare_mode == 'GE':
                min_amount = 0.0
                max_amount = len(island['vertices']) * (1 + threshold_verts / 100)
            else:   # EQ
                min_amount = len(island['vertices']) * (1 - threshold_verts / 100)
                max_amount = len(island['vertices']) * (1 + threshold_verts / 100)
            # edges threshold
            edges_len = sum([_edge.calc_length() for _edge in island['edges']])
            if compare_mode == 'LE':
                min_len = edges_len * (1 - threshold_edges / 100)
                max_len = sys.maxsize
            elif compare_mode == 'GE':
                min_len = 0.0
                max_len = edges_len * (1 + threshold_edges / 100)
            else:  # EQ
                min_len = edges_len * (1 - threshold_edges / 100)
                max_len = edges_len * (1 + threshold_edges / 100)
            # faces threshold
            faces_area = sum([_face.calc_area() for _face in island['faces']])
            if compare_mode == 'LE':
                min_area = faces_area * (1 - threshold_area / 100)
                max_area = sys.maxsize
            elif compare_mode == 'GE':
                min_area = 0.0
                max_area = faces_area * (1 + threshold_area / 100)
            else:  # EQ
                min_area = faces_area * (1 - threshold_area / 100)
                max_area = faces_area * (1 + threshold_area / 100)
            # make selection
            if op_mode == 'OR':
                if (mode_verts and any(min_amount <= value <= max_amount for value in vertices_amounts)) \
                        or (mode_edges and any(min_len <= value <= max_len for value in edges_length)) \
                        or (mode_area and any(min_area <= value <= max_area for value in faces_areas)):
                    cls._select_island(island=island)
            elif op_mode == 'AND':
                # combine all possible conditions by verts/edges/area
                conditions = []
                if mode_verts:
                    conditions.append(any(min_amount <= value <= max_amount for value in vertices_amounts))
                if mode_edges:
                    conditions.append(any(min_len <= value <= max_len for value in edges_length))
                if mode_area:
                    conditions.append(any(min_area <= value <= max_area for value in faces_areas))
                if conditions and all(conditions):
                    cls._select_island(island=island)
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        # report
        if len(selected_islands) == 1:
            selected_island_idx = selected_islands[0]
            # if there is only one selected island - show its values with threshold
            sum_edges_length = sum([_edge.calc_length() for _edge in db[selected_island_idx]['edges']])
            sum_faces_area = sum([_face.calc_area() for _face in db[selected_island_idx]['faces']])
            op.report(
                type={'INFO'},
                message='Values: v=' \
                        + str(len(db[selected_island_idx]["vertices"])) \
                        + '-' + str(round(len(db[selected_island_idx]["vertices"]) * threshold_verts / 100, 3)) \
                        + ' | e=' \
                        + str(round(sum_edges_length, 3)) \
                        + '-' + str(round(sum_edges_length * threshold_edges / 100, 3)) \
                        + ' | f=' \
                        + str(round(sum_faces_area, 3)) \
                        + '-' + str(round(sum_faces_area * threshold_area / 100, 3))
                )
        print('Islands by Comb executed in : ' + str(time.time() - start_time) + ' sec.')

    @classmethod
    def islands_decompose(cls, context, offset=0.5):
        src_obj = context.active_object
        start_time = time.time()
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # get islands db
        db, bm = cls.islands(obj=src_obj)
        # decompose selected islands
        shift_step = 0
        for island in db:
            # if fully selected
            if all(vertex.select for vertex in island['vertices']):
                # shift vertically by offset
                if shift_step != 0: # don't shift first island (on first step)
                    for vertex in island['vertices']:
                        vertex.co.z += shift_step * offset
                shift_step += 1
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Islands Decompose executed in : ' + str(time.time() - start_time) + ' sec.')

    @staticmethod
    def _select_island(island):
        # select all vertices/edges/faces of the island
        for vertex in island['vertices']:
            vertex.select = True
        for edge in island['edges']:
            edge.select = True
        for face in island['faces']:
            face.select = True

    @staticmethod
    def _deselect_island(island):
        # deselect all vertices/edges/faces of the island
        for vertex in island['vertices']:
            vertex.select = False
        for edge in island['edges']:
            edge.select = False
        for face in island['faces']:
            face.select = False

    @staticmethod
    def ui(layout, context):
        # ui panel
        # Dec Select
        layout.operator(
            operator='island_tools.dec_select',
            icon='ZOOM_SELECTED'        )
        # Islands decompose
        col = layout.column(align=True)
        op = col.operator(
            operator='island_tools.decompose',
            icon='SEQ_SEQUENCER',
            text='Decompose'
        )
        op.offset = context.scene.island_tools_prop_decompose_offset
        col.prop(
            data=context.scene,
            property='island_tools_prop_decompose_offset',
            text='Offset'
        )
        # select islands
        layout.label(text='Select Islands By:')
        op = layout.operator(
            operator='island_tools.islands_by',
            icon='GROUP_VERTEX',
            text='Filter Islands'
        )
        op.op_mode = context.scene.island_tools_prop_islands_by_op_mode
        op.compare_mode = context.scene.island_tools_prop_islands_by_compare_mode
        op.mode_verts = context.scene.island_tools_prop_islands_by_mode_verts
        op.threshold_verts = context.scene.island_tools_prop_islands_by_threshold_verts
        op.mode_edges = context.scene.island_tools_prop_islands_by_mode_edges
        op.threshold_edges = context.scene.island_tools_prop_islands_by_threshold_edges
        op.mode_area = context.scene.island_tools_prop_islands_by_mode_area
        op.threshold_area = context.scene.island_tools_prop_islands_by_threshold_area
        row = layout.row(align=True)
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_op_mode',
            expand=True
        )
        row = layout.row(align=True)
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_compare_mode',
            expand=True
        )
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_mode_verts'
        )
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_threshold_verts',
            text='% Threshold'
        )
        row = col.row(align=True)
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_mode_edges'
        )
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_threshold_edges',
            text='% Threshold'
        )
        row = col.row(align=True)
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_mode_area'
        )
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_threshold_area',
            text='% Threshold'
        )


# OPERATORS

class IslandTools_OT_dec_select(Operator):
    bl_idname = 'island_tools.dec_select'
    bl_label = 'Dec Select'
    bl_description = 'Decrease selected islands to full selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        IslandTools.dec_select(
            context=context
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

class IslandTools_OT_islands_by(Operator):
    bl_idname = 'island_tools.islands_by'
    bl_label = 'Select Islands By'
    bl_description = 'Select islands by specified mode'
    bl_options = {'REGISTER', 'UNDO'}

    op_mode = EnumProperty(
        name='Op Mode',
        items=[
            ('OR', 'OR', 'OR'),
            ('AND', 'AND', 'AND')
        ],
        default='OR'
    )

    compare_mode = EnumProperty(
        name='Compare Mode',
        items=[
            ('EQ', '==', '=='),
            ('LE', '<=', '<='),
            ('GE', '>=', '>=')
        ],
        default='EQ'
    )

    mode_verts = BoolProperty(
        name='Verts',
        default=False
    )

    threshold_verts = FloatProperty(
        name='Threshold %',
        default=0.0
    )

    mode_edges = BoolProperty(
        name='Edges',
        default=False
    )

    threshold_edges = FloatProperty(
        name='Threshold %',
        default=5.0
    )

    mode_area = BoolProperty(
        name='Area',
        default=False
    )

    threshold_area = FloatProperty(
        name='Threshold %',
        default=5.0
    )

    def execute(self, context):
        IslandTools.select_islands_by(
            context=context,
            op=self,
            op_mode=self.op_mode,
            compare_mode=self.compare_mode,
            mode_verts=self.mode_verts,
            mode_edges=self.mode_edges,
            mode_area=self.mode_area,
            threshold_verts=self.threshold_verts,
            threshold_edges=self.threshold_edges,
            threshold_area=self.threshold_area
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

class IslandTools_OT_decompose(Operator):
    bl_idname = 'island_tools.decompose'
    bl_label = 'Islands Decompose'
    bl_description = 'Decompose selected islands vertically'
    bl_options = {'REGISTER', 'UNDO'}

    offset = FloatProperty(
        name='Decompose Offset',
        default=0.5
    )

    def execute(self, context):
        IslandTools.islands_decompose(
            context=context,
            offset=self.offset
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'


# PANELS

class IslandTools_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Island Tools'
    bl_category = '1D'

    def draw(self, context):
        IslandTools.ui(
            layout=self.layout,
            context=context
        )


# REGISTER

def register(ui=True):
    Scene.island_tools_prop_islands_by_op_mode = EnumProperty(
        name='Op Mode',
        items=[
            ('OR', 'OR', 'OR'),
            ('AND', 'AND', 'AND')
        ],
        default='AND'
    )
    Scene.island_tools_prop_islands_by_compare_mode = EnumProperty(
        name='Compare Mode',
        items=[
            ('EQ', '==', '=='),
            ('LE', '<=', '<='),
            ('GE', '>=', '>=')
        ],
        default='EQ'
    )
    Scene.island_tools_prop_islands_by_mode_verts = BoolProperty(
        name='Verts',
        default=False
    )
    Scene.island_tools_prop_islands_by_mode_edges = BoolProperty(
        name='Edges',
        default=False
    )
    Scene.island_tools_prop_islands_by_mode_area = BoolProperty(
        name='Area',
        default=False
    )
    Scene.island_tools_prop_islands_by_threshold_verts = FloatProperty(
        name='Islands by Verts Threshold',
        default=0.0,
        min=0.0
    )
    Scene.island_tools_prop_islands_by_threshold_edges = FloatProperty(
        name='Islands by Edges Threshold',
        default=5.0,
        min=0.0
    )
    Scene.island_tools_prop_islands_by_threshold_area = FloatProperty(
        name='Islands by Area Threshold',
        default=5.0,
        min=0.0
    )
    Scene.island_tools_prop_decompose_offset = FloatProperty(
        name='Decompose Offset',
        default=0.5
    )
    register_class(IslandTools_OT_dec_select)
    register_class(IslandTools_OT_islands_by)
    register_class(IslandTools_OT_decompose)
    if ui:
        register_class(IslandTools_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(IslandTools_PT_panel)
    unregister_class(IslandTools_OT_decompose)
    unregister_class(IslandTools_OT_islands_by)
    unregister_class(IslandTools_OT_dec_select)
    del Scene.island_tools_prop_decompose_offset
    del Scene.island_tools_prop_islands_by_threshold_area
    del Scene.island_tools_prop_islands_by_threshold_edges
    del Scene.island_tools_prop_islands_by_threshold_verts
    del Scene.island_tools_prop_islands_by_mode_area
    del Scene.island_tools_prop_islands_by_mode_edges
    del Scene.island_tools_prop_islands_by_mode_verts
    del Scene.island_tools_prop_islands_by_compare_mode
    del Scene.island_tools_prop_islands_by_op_mode


if __name__ == "__main__":
    register()
