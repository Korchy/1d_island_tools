# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_island_tools

import bmesh
import bpy
from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class
# import itertools

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

    @classmethod
    def create_islands_db(cls, context):
        # Create list of islands of active mesh
        src_obj = context.active_object
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # bm object
        bm = bmesh.new()
        bm.from_mesh(src_obj.data)
        bm.edges.ensure_lookup_table()
        # create islands db

        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        bm.free()
        # return mode back
        context.scene.objects.active = src_obj
        bpy.ops.object.mode_set(mode=mode)

    @classmethod
    def dec_select(cls, context):
        # Decrease selection to whole selected islands
        src_obj = context.active_object
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # bm object
        bm = bmesh.new()
        bm.from_mesh(src_obj.data)
        bm.edges.ensure_lookup_table()
        # remove selection from partially selected islands

        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        bm.free()
        # return mode back
        context.scene.objects.active = src_obj
        bpy.ops.object.mode_set(mode=mode)

    @classmethod
    def islands_by_verts_amount(cls, context):
        # Select islands with the same vertices amount as already selected islands
        src_obj = context.active_object
        # current mode
        mode = src_obj.mode
        # switch to OBJECT mode
        if src_obj.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # bm object
        bm = bmesh.new()
        bm.from_mesh(src_obj.data)
        bm.edges.ensure_lookup_table()
        # select islands

        # save changed data to mesh
        bm.to_mesh(src_obj.data)
        bm.free()
        # return mode back
        context.scene.objects.active = src_obj
        bpy.ops.object.mode_set(mode=mode)

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
        # Create Islands DB
        layout.operator(
            operator='island_tools.create_islands_db',
            icon='SCENE_DATA'
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

class IslandTools_OT_create_db(Operator):
    bl_idname = 'island_tools.create_islands_db'
    bl_label = 'Create Islands DB'
    bl_description = 'Create islands DB'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        IslandTools.create_islands_db(
            context=context
        )
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

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
    register_class(IslandTools_OT_create_db)
    register_class(IslandTools_OT_dec_select)
    register_class(IslandTools_OT_islands_by_verts_amount)
    if ui:
        register_class(IslandTools_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(IslandTools_PT_panel)
    unregister_class(IslandTools_OT_islands_by_verts_amount)
    unregister_class(IslandTools_OT_dec_select)
    unregister_class(IslandTools_OT_create_db)


if __name__ == "__main__":
    register()
