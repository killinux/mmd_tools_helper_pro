bl_info = {
    "name": "MMD tools helper",
    "author": "Hogarth-MMD",
    "version": (2, 4),
    "blender": (3, 6, 0),  # 更新为Blender 3.6版本
    "location": "View3D > Sidebar > MMD Tools Helper",  # 位置更新为侧边栏
    "description": "various mmd_tools helper scripts",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

import bpy
import importlib  # 替换imp模块为importlib

class MMDToolsHelperPanel(bpy.types.Panel):
    """Creates the MMD Tools Helper Panel in VIEW_3D UI tab"""
    bl_label = "MMD Tools Helper"
    bl_idname = "OBJECT_PT_mmd_tools_helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+使用UI替代TOOLS
    bl_category = "mmd_tools_helper"  # 侧边栏中的标签名称

    def draw(self, context):
        print("init--draw")
        layout = self.layout
        row = layout.row()
        # 可以在这里添加面板默认内容


# 导入子模块
from . import (
    model,
    mmd_view,
    mmd_lamp_setup,
    convert_to_blender_camera,
    background_color_picker,
    boneMaps_renamer,
    replace_bones_renaming,
    armature_diagnostic,
    add_foot_leg_ik,
    add_hand_arm_ik,
    display_panel_groups,
    toon_textures_to_node_editor_shader,
    toon_modifier,
    reverse_japanese_english,
    miscellaneous_tools,
    blender_bone_names_to_japanese_bone_names
)

# 使用importlib.reload替代imp.reload
importlib.reload(model)
importlib.reload(mmd_view)
importlib.reload(mmd_lamp_setup)
importlib.reload(convert_to_blender_camera)
importlib.reload(background_color_picker)
importlib.reload(boneMaps_renamer)
importlib.reload(replace_bones_renaming)
importlib.reload(armature_diagnostic)
importlib.reload(add_foot_leg_ik)
importlib.reload(add_hand_arm_ik)
importlib.reload(display_panel_groups)
importlib.reload(toon_textures_to_node_editor_shader)
importlib.reload(toon_modifier)
importlib.reload(reverse_japanese_english)
importlib.reload(miscellaneous_tools)
importlib.reload(blender_bone_names_to_japanese_bone_names)


def register():
    bpy.utils.register_class(MMDToolsHelperPanel)
    # 确保子模块中的类也被注册
    #model.register()
    mmd_view.register()
    mmd_lamp_setup.register()
    convert_to_blender_camera.register()
    background_color_picker.register()
    boneMaps_renamer.register()
    replace_bones_renaming.register()
    armature_diagnostic.register()
    add_foot_leg_ik.register()
    add_hand_arm_ik.register()
    display_panel_groups.register()
    toon_textures_to_node_editor_shader.register()
    toon_modifier.register()
    reverse_japanese_english.register()
    miscellaneous_tools.register()
    blender_bone_names_to_japanese_bone_names.register()


def unregister():
    bpy.utils.unregister_class(MMDToolsHelperPanel)
    # 确保子模块中的类也被注销
    #model.unregister()
    mmd_view.unregister()
    mmd_lamp_setup.unregister()
    convert_to_blender_camera.unregister()
    background_color_picker.unregister()
    boneMaps_renamer.unregister()
    replace_bones_renaming.unregister()
    armature_diagnostic.unregister()
    add_foot_leg_ik.unregister()
    add_hand_arm_ik.unregister()
    display_panel_groups.unregister()
    toon_textures_to_node_editor_shader.unregister()
    toon_modifier.unregister()
    reverse_japanese_english.unregister()
    miscellaneous_tools.unregister()
    blender_bone_names_to_japanese_bone_names.unregister()


if __name__ == "__main__":
    register()
