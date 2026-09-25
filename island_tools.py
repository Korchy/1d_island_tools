# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_island_tools

import time
import bmesh
import bpy
from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "Island Tools",
    "description": "Toolset for working with mesh islands",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Tool panel > 1D > Island Tools",
    "doc_url": "https://github.com/Korchy/1d_island_tools",
    "tracker_url": "https://github.com/Korchy/1d_island_tools",
    "category": "All"
}


# MAIN CLASS

class IslandTools:

    # islands_db - list of lists of vertices. Each list of vertices is an "island" - separated part of the mesh
    islands_db = None   # static pointer to islands db
    bm = None           # static BMesh object from which db was created

    @classmethod
    def db(cls, obj, force_update=False):
        # singleton for getting islands db
        if (cls.islands_db is None) or force_update:
            cls.update_db(obj=obj)
        return cls.islands_db, cls.bm

    @classmethod
    def update_db(cls, obj):
        # create/update islands db for object
        start_time = time.time()
        # create BMesh object
        cls.bm = bmesh.new()
        cls.bm.from_mesh(obj.data)
        # cls.bm.verts.ensure_lookup_table()
        # create islands db from BMesh object
        cls.islands_db = []
        checked = set() # already checked vertices
        # check all vertices of the mesh
        for vert in cls.bm.verts:
            if vert in checked:
                continue
            checked.add(vert)
            # current island
            # island = []
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
            cls.islands_db.append(
                {
                    'vertices': vertices,
                    'edges': edges,
                    'faces': faces
                }
            )
        print('Islands DB (re)created in : ' + str(time.time() - start_time) \
              + ' sec, got ' + str(len(cls.islands_db)) + ' islands.')

    @classmethod
    def update_islands_db(cls, context):
        # Create list of islands of active mesh
        src_obj = context.active_object
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # create/update islands db
        cls.db(obj=src_obj, force_update=True)
        # return mode back
        context.scene.objects.active = src_obj
        bpy.ops.object.mode_set(mode=mode)

    @classmethod
    def free_islands_db(cls):
        # free islands db
        cls.islands_db = None
        if cls.bm is not None:
            cls.bm.free()
            cls.bm = None

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
        db, bm = cls.db(obj=src_obj)
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
    def islands_by_verts_amount(cls, context):
        # Select islands with the same vertices amount as already selected islands
        src_obj = context.active_object
        start_time = time.time()
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # get islands db
        db, bm = cls.db(obj=src_obj)
        # select islands
        vertices_amounts = set()
        # collect amount of vertices for fully selected islands
        for island in db:
            # collect full selected islands by vertices amount
            if all(vertex.select for vertex in island['vertices']):
                vertices_amounts.add(len(island['vertices']))
            # if island is partially selected - remove selection
            if any(not vertex.select for vertex in island['vertices']):
                for vertex in island['vertices']:
                    vertex.select = False
                for edge in island['edges']:
                    edge.select = False
                for face in island['faces']:
                    face.select = False
        # select islands with same amount of vertices
        for island in db:
            if len(island['vertices']) in vertices_amounts:
                for vertex in island['vertices']:
                    vertex.select = True
                for edge in island['edges']:
                    edge.select = True
                for face in island['faces']:
                    face.select = True
        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        # return mode back
        bpy.ops.object.mode_set(mode=mode)
        print('Islands by Verts Amount executed in : ' + str(time.time() - start_time) + ' sec.')

    @staticmethod
    def _deselect_all(bm):
        # remove all selection from edges and vertices in bmesh
        for face in bm.faces:
            face.select = False
        for edge in bm.edges:
            edge.select = False
        for vertex in bm.verts:
            vertex.select = False

    @staticmethod
    def ui(layout):
        # ui panel
        # Create/Update/Free Islands DB
        row = layout.row(align=True)
        row.operator(
            operator='island_tools.update_islands_db',
            icon='SCENE_DATA',
            text = 'Create DB'
        )
        row.operator(
            operator='island_tools.free_islands_db',
            icon='CANCEL',
            text = 'Free DB'
        )
        # Dec Select
        layout.operator(
            operator='island_tools.dec_select',
            icon='ZOOM_SELECTED'
        )
        # Select islands by vertices amount
        layout.operator(
            operator='island_tools.islands_by_verts_amount',
            icon='GROUP_VERTEX'
        )


# OPERATORS

class IslandTools_OT_update_db(Operator):
    bl_idname = 'island_tools.update_islands_db'
    bl_label = 'Create/Update Islands DB'
    bl_description = 'Create/Update islands DB'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        IslandTools.update_islands_db(
            context=context
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

class IslandTools_OT_free_db(Operator):
    bl_idname = 'island_tools.free_islands_db'
    bl_label = 'Free Islands DB'
    bl_description = 'Free islands DB'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        IslandTools.free_islands_db()
        return {'FINISHED'}

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

class IslandTools_OT_islands_by_verts_amount(Operator):
    bl_idname = 'island_tools.islands_by_verts_amount'
    bl_label = 'Islands By Verts Amount'
    bl_description = 'Select islands with the same amount of vertices as already selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        IslandTools.islands_by_verts_amount(
            context=context
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
            layout=self.layout
        )


# REGISTER

def register(ui=True):
    register_class(IslandTools_OT_update_db)
    register_class(IslandTools_OT_free_db)
    register_class(IslandTools_OT_dec_select)
    register_class(IslandTools_OT_islands_by_verts_amount)
    if ui:
        register_class(IslandTools_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(IslandTools_PT_panel)
    unregister_class(IslandTools_OT_islands_by_verts_amount)
    unregister_class(IslandTools_OT_dec_select)
    unregister_class(IslandTools_OT_free_db)
    unregister_class(IslandTools_OT_update_db)


if __name__ == "__main__":
    register()
