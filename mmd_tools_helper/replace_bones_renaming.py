import bpy
from . import model

# 定义场景属性
def register_props():
    bpy.types.Scene.find_bone_string = bpy.props.StringProperty(
        name="查找字符串",
        description="在骨骼名称中查找此字符串",
        default=""
    )
    bpy.types.Scene.replace_bone_string = bpy.props.StringProperty(
        name="替换字符串",
        description="用于替换的字符串",
        default=""
    )
    bpy.types.Scene.bones_all_or_selected = bpy.props.BoolProperty(
        name="仅选中骨骼",
        description="只处理选中的骨骼",
        default=False
    )

def unregister_props():
    del bpy.types.Scene.find_bone_string
    del bpy.types.Scene.replace_bone_string
    del bpy.types.Scene.bones_all_or_selected

class ReplaceBonesRenamingPanel(bpy.types.Panel):
    """骨骼批量重命名面板"""
    bl_label = "骨骼批量重命名工具"
    bl_idname = "OBJECT_PT_replace_bones_renaming"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 替换了TOOLS，适用于Blender 2.8+
    bl_category = "mmd_tools_helper"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.label(text="骨骼名称替换")
        
        box.prop(scene, "find_bone_string", text="查找")
        box.prop(scene, "replace_bone_string", text="替换为")
        box.prop(scene, "bones_all_or_selected")
        
        box.operator("mmd_tools_helper.replace_bones_renaming", 
                     text="执行替换")

def main(context):
    # 查找并设置活动电枢对象
    armature = model.findArmature(context.active_object)
    if armature:
        context.view_layer.objects.active = armature  # 适用于Blender 2.8+的API
        
        # 获取要处理的骨骼
        if context.scene.bones_all_or_selected:
            bones_to_process = [b for b in armature.data.bones if b.select]
        else:
            bones_to_process = armature.data.bones
            
        # 处理骨骼名称
        find_str = context.scene.find_bone_string
        replace_str = context.scene.replace_bone_string
        
        if find_str:  # 只有当查找字符串不为空时才执行替换
            for bone in bones_to_process:
                # 跳过包含特定关键词的骨骼
                if 'dummy' not in bone.name and 'shadow' not in bone.name:
                    bone.name = bone.name.replace(find_str, replace_str)

class ReplaceBonesRenaming(bpy.types.Operator):
    """批量查找并替换骨骼名称"""
    bl_idname = "mmd_tools_helper.replace_bones_renaming"
    bl_label = "替换骨骼名称"
    bl_options = {'REGISTER', 'UNDO'}  # 添加撤销支持

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "骨骼名称替换完成")
        return {'FINISHED'}

def register():
    register_props()
    bpy.utils.register_class(ReplaceBonesRenamingPanel)
    bpy.utils.register_class(ReplaceBonesRenaming)

def unregister():
    unregister_props()
    bpy.utils.unregister_class(ReplaceBonesRenamingPanel)
    bpy.utils.unregister_class(ReplaceBonesRenaming)

if __name__ == "__main__":
    register()
