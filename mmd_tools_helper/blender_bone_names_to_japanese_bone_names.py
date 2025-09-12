import bpy
from . import model

class BlenderToJapaneseBoneNamesPanel(bpy.types.Panel):
    """Creates a Panel"""
    bl_idname = "OBJECT_PT_blender_to_japanese_bone_names"
    bl_label = "Copy Blender bone names to Japanese bone names"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+ 中使用UI替代TOOLS
    bl_category = "mmd_tools_helper"  # 在N面板中显示的类别名称

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row.label(text="Copy Blender bone names to Japanese bone names", icon="TEXT")
        row = layout.row()
        row.operator("mmd_tools_helper.blender_to_japanese_bone_names", 
                    text="Copy Blender bone names to Japanese bone names")
        row = layout.row()

def main(context):
    # 获取当前选中对象的骨架
    armature = model.findArmature(bpy.context.active_object)
    if armature is None:
        return
    
    # 遍历所有骨骼并复制名称
    for b in armature.data.bones:
        pose_bone = armature.pose.bones.get(b.name)
        if pose_bone and hasattr(pose_bone, "mmd_bone"):
            pose_bone.mmd_bone.name_j = b.name

class BlenderToJapaneseBoneNames(bpy.types.Operator):
    """Copy Blender bone names to Japanese bone names"""
    bl_idname = "mmd_tools_helper.blender_to_japanese_bone_names"
    bl_label = "Copy Blender bone names to Japanese bone names"
    bl_options = {'REGISTER', 'UNDO'}  # 添加撤销支持

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "Bone names copied successfully")  # 添加操作反馈
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BlenderToJapaneseBoneNames)
    bpy.utils.register_class(BlenderToJapaneseBoneNamesPanel)

def unregister():
    bpy.utils.unregister_class(BlenderToJapaneseBoneNames)
    bpy.utils.unregister_class(BlenderToJapaneseBoneNamesPanel)

if __name__ == "__main__":
    register()
#register()