# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_island_tools

import time
import bmesh
import bpy
from bpy.props import FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "Island Tools",
    "description": "Toolset for working with mesh islands",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 1, 0),
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
    def islands_by_verts(cls, context, threshold=5.0):
        # Select islands with the close by threshold vertices amount as already selected islands
        #   threshold - %
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
        # collect amount of vertices for fully selected islands
        for island in db:
            # collect full selected islands by vertices amount
            if all(vertex.select for vertex in island['vertices']):
                vertices_amounts.add(len(island['vertices']))
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                cls._deselect_island(island=island)
        # select islands with close amount of vertices
        for island in db:
            min_amount = len(island['vertices']) * (1 - threshold / 100)
            max_amount = len(island['vertices']) * (1 + threshold / 100)
            if any(min_amount <= value <= max_amount for value in vertices_amounts):
                cls._select_island(island=island)
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Islands by Verts executed in : ' + str(time.time() - start_time) + ' sec.')

    @classmethod
    def islands_by_edges(cls, context, threshold=5.0):
        # Select islands with close by threshold summary edges length as already selected islands
        #   threshold - %
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
        edges_length = set()
        # collect summary edges length for fully selected islands
        for island in db:
            # collect summary edges length for full selected islands
            if all(vertex.select for vertex in island['vertices']):
                edges_length.add(sum([_edge.calc_length() for _edge in island['edges']]))
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                cls._deselect_island(island=island)
        # select islands with close amount of summary edges length
        for island in db:
            edges_len = sum([_edge.calc_length() for _edge in island['edges']])
            min_len = edges_len * (1 - threshold / 100)
            max_len = edges_len * (1 + threshold / 100)
            if any(min_len <= value <= max_len for value in edges_length):
                cls._select_island(island=island)
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Islands by Edges executed in : ' + str(time.time() - start_time) + ' sec.')

    @classmethod
    def islands_by_area(cls, context, threshold=5.0):
        # Select islands with close by threshold summary faces area as already selected islands
        #   threshold - %
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
        faces_areas = set()
        # collect summary faces area for fully selected islands
        for island in db:
            # collect summary faces area for full selected islands
            if all(vertex.select for vertex in island['vertices']):
                faces_areas.add(sum([_face.calc_area() for _face in island['faces']]))
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                cls._deselect_island(island=island)
        # select islands with close amount of summary edges length
        for island in db:
            faces_area = sum([_face.calc_area() for _face in island['faces']])
            min_area = faces_area * (1 - threshold / 100)
            max_area = faces_area * (1 + threshold / 100)
            if any(min_area <= value <= max_area for value in faces_areas):
                cls._select_island(island=island)
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Islands by Area executed in : ' + str(time.time() - start_time) + ' sec.')

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
            icon='ZOOM_SELECTED'
        )
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
        col = layout.column(align=True)
        # Select islands by vertices
        row = col.row(align=True)
        op = row.operator(
            operator='island_tools.islands_by_verts',
            icon='UV_VERTEXSEL',
            text='Verts'
        )
        op.threshold = context.scene.island_tools_prop_islands_by_verts_threshold
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_verts_threshold',
            text='% Threshold'
        )
        # Select islands by edges
        row = col.row(align=True)
        op = row.operator(
            operator='island_tools.islands_by_edges',
            icon='UV_EDGESEL',
            text='Edges'
        )
        op.threshold = context.scene.island_tools_prop_islands_by_edges_threshold
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_edges_threshold',
            text='% Threshold'
        )
        # Select islands by area
        row = col.row(align=True)
        op = row.operator(
            operator='island_tools.islands_by_area',
            icon='UV_FACESEL',
            text='Area'
        )
        op.threshold = context.scene.island_tools_prop_islands_by_area_threshold
        row.prop(
            data=context.scene,
            property='island_tools_prop_islands_by_area_threshold',
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

class IslandTools_OT_islands_by_verts(Operator):
    bl_idname = 'island_tools.islands_by_verts'
    bl_label = 'Islands By Verts'
    bl_description = 'Select islands with the same amount of vertices as already selected'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = FloatProperty(
        name='Threshold %',
        default=5.0
    )

    def execute(self, context):
        IslandTools.islands_by_verts(
            context=context,
            threshold=self.threshold
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

class IslandTools_OT_islands_by_edges(Operator):
    bl_idname = 'island_tools.islands_by_edges'
    bl_label = 'Islands By Edges'
    bl_description = 'Select islands with the same summary length of edges as already selected'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = FloatProperty(
        name='Threshold %',
        default=5.0
    )

    def execute(self, context):
        IslandTools.islands_by_edges(
            context=context,
            threshold=self.threshold
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

class IslandTools_OT_islands_by_area(Operator):
    bl_idname = 'island_tools.islands_by_area'
    bl_label = 'Islands By Area'
    bl_description = 'Select islands with the same summary area of faces as already selected'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = FloatProperty(
        name='Threshold %',
        default=5.0
    )

    def execute(self, context):
        IslandTools.islands_by_area(
            context=context,
            threshold=self.threshold
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
    Scene.island_tools_prop_islands_by_verts_threshold = FloatProperty(
        name='Islands by Verts Threshold',
        default=5.0,
        min=0.0001
    )
    Scene.island_tools_prop_islands_by_edges_threshold = FloatProperty(
        name='Islands by Edges Threshold',
        default=5.0,
        min=0.0001
    )
    Scene.island_tools_prop_islands_by_area_threshold = FloatProperty(
        name='Islands by Area Threshold',
        default=5.0,
        min=0.0001
    )
    Scene.island_tools_prop_decompose_offset = FloatProperty(
        name='Decompose Offset',
        default=0.5
    )
    register_class(IslandTools_OT_dec_select)
    register_class(IslandTools_OT_islands_by_verts)
    register_class(IslandTools_OT_islands_by_edges)
    register_class(IslandTools_OT_islands_by_area)
    register_class(IslandTools_OT_decompose)
    if ui:
        register_class(IslandTools_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(IslandTools_PT_panel)
    unregister_class(IslandTools_OT_decompose)
    unregister_class(IslandTools_OT_islands_by_area)
    unregister_class(IslandTools_OT_islands_by_edges)
    unregister_class(IslandTools_OT_islands_by_verts)
    unregister_class(IslandTools_OT_dec_select)
    del Scene.island_tools_prop_decompose_offset
    del Scene.island_tools_prop_islands_by_area_threshold
    del Scene.island_tools_prop_islands_by_edges_threshold
    del Scene.island_tools_prop_islands_by_verts_threshold


if __name__ == "__main__":
    register()
