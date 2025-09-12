import bpy
from . import model

# ------------------------------
# 1. 场景属性注册（避免属性残留，符合Blender 3.x规范）
# ------------------------------
def register_scene_properties():
    # 查找字符串：骨骼名称中需替换的目标文本
    bpy.types.Scene.find_bone_string = bpy.props.StringProperty(
        name="Find String",
        description="Text to search for in bone names",
        default="",
        subtype='NONE'
    )
    # 替换字符串：用于替换的新文本
    bpy.types.Scene.replace_bone_string = bpy.props.StringProperty(
        name="Replace With",
        description="Text to replace the found string",
        default="",
        subtype='NONE'
    )
    # 仅处理选中骨骼的开关（True=选中骨骼，False=所有骨骼）
    bpy.types.Scene.bones_all_or_selected = bpy.props.BoolProperty(
        name="Selected Bones Only",
        description="Apply replacement only to selected bones (uncheck for all)",
        default=False
    )

def unregister_scene_properties():
    # 注销时清理属性，防止残留
    if hasattr(bpy.types.Scene, "find_bone_string"):
        del bpy.types.Scene.find_bone_string
    if hasattr(bpy.types.Scene, "replace_bone_string"):
        del bpy.types.Scene.replace_bone_string
    if hasattr(bpy.types.Scene, "bones_all_or_selected"):
        del bpy.types.Scene.bones_all_or_selected

# ------------------------------
# 2. 面板类（适配Blender 3.6侧边栏，按N键显示）
# ------------------------------
class ReplaceBonesRenamingPanel(bpy.types.Panel):
    """骨骼批量重命名面板"""
    bl_label = "Bone Batch Rename"
    bl_idname = "OBJECT_PT_replace_bones_renaming"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 关键：Blender 2.8+ 用UI替代废弃的TOOLS
    bl_category = "mmd_tools_helper"  # 面板归类到MMD工具助手
    bl_order = 5  # 侧边栏中的显示顺序（可选）

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 查找字符串输入区
        row = layout.row()
        row.label(text="Find in Bone Names:")
        row = layout.row()
        row.prop(scene, "find_bone_string", text="")

        # 替换字符串输入区
        row = layout.row()
        row.label(text="Replace With:")
        row = layout.row()
        row.prop(scene, "replace_bone_string", text="")

        # 选中骨骼开关
        row = layout.row()
        row.prop(scene, "bones_all_or_selected")

        # 执行按钮（带图标+放大，提升体验）
        row = layout.row()
        row.scale_y = 1.3
        row.operator(
            "mmd_tools_helper.replace_bones_renaming",
            text="Find & Replace Bone Names",
            icon="RENAME_OBJECT"
        )

# ------------------------------
# 3. 核心功能（修复编辑模式，确保骨骼名称可修改）
# ------------------------------
def main(context):
    # 获取骨架对象（增强错误检查）
    armature = model.findArmature(context.active_object)
    if not armature:
        raise Exception("No armature found! Select a model with an armature first.")
    
    find_str = context.scene.find_bone_string
    replace_str = context.scene.replace_bone_string
    use_selected = context.scene.bones_all_or_selected
    renamed_count = 0

    # 切换到编辑模式（Blender要求：修改骨骼名称必须在编辑模式）
    original_mode = armature.mode
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    try:
        for bone in edit_bones:
            # 条件1：仅处理选中骨骼（若开关开启）
            if use_selected and not bone.select:
                continue
            # 条件2：排除dummy/shadow骨骼（大小写不敏感）
            if "dummy" in bone.name.lower() or "shadow" in bone.name.lower():
                continue
            # 条件3：找到目标字符串才替换
            if find_str in bone.name:
                bone.name = bone.name.replace(find_str, replace_str)
                renamed_count += 1
    finally:
        # 无论是否出错，恢复原模式
        bpy.ops.object.mode_set(mode=original_mode)

    return renamed_count

# ------------------------------
# 4. 操作符类（支持撤销+错误反馈）
# ------------------------------
class ReplaceBonesRenaming(bpy.types.Operator):
    """批量重命名骨骼（排除dummy/shadow骨骼）"""
    bl_idname = "mmd_tools_helper.replace_bones_renaming"
    bl_label = "Bone Batch Rename"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销
    bl_description = "Find and replace text in bone names"

    @classmethod
    def poll(cls, context):
        # 按钮启用条件：有活跃对象且存在骨架
        return context.active_object and model.findArmature(context.active_object)

    def execute(self, context):
        try:
            renamed_count = main(context)
            if renamed_count == 0:
                self.report({'INFO'}, "No bones matched (or all were dummy/shadow)")
            else:
                self.report({'INFO'}, f"Success! Renamed {renamed_count} bone(s)")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# ------------------------------
# 5. 注册/注销
# ------------------------------
def register():
    register_scene_properties()
    bpy.utils.register_class(ReplaceBonesRenamingPanel)
    bpy.utils.register_class(ReplaceBonesRenaming)

def unregister():
    bpy.utils.unregister_class(ReplaceBonesRenamingPanel)
    bpy.utils.unregister_class(ReplaceBonesRenaming)
    unregister_scene_properties()

if __name__ == "__main__":
    register()