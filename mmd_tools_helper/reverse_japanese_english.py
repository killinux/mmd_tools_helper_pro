import bpy

# ------------------------------
# 面板类（适配Blender 3.6侧边栏）
# ------------------------------
class ReverseJapaneseEnglishPanel(bpy.types.Panel):
    """交换MMD模型中的日文和英文名称"""
    bl_idname = "OBJECT_PT_reverse_japanese_english"
    bl_label = "MMD Name Swapper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 关键：替换废弃的TOOLS为UI（侧边栏显示）
    bl_category = "mmd_tools_helper"
    bl_order = 9  # 面板显示顺序

    def draw(self, context):
        layout = self.layout
        layout.label(text="Swap Japanese/English Names", icon="TEXT")
        layout.operator(
            "mmd_tools_helper.reverse_japanese_english",
            text="Swap Names"
        )

# ------------------------------
# 主功能实现
# ------------------------------
def main(context):
    # 1. 交换材质的日文和英文名称
    for material in bpy.data.materials:
        # 检查是否有MMD材质属性
        if hasattr(material, 'mmd_material'):
            mmd_mat = material.mmd_material
            # 保存原始名称
            original_j = mmd_mat.name_j
            original_e = mmd_mat.name_e
            
            # 仅当英文名不为空时交换
            if original_e:
                mmd_mat.name_j = original_e
                mmd_mat.name_e = original_j
                # 更新材质本身的名称
                material.name = original_e

    # 2. 交换骨骼的日文和英文名称
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    for armature in armatures:
        # 激活当前骨架并切换到POSE模式
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        
        # 遍历所有骨骼
        for pose_bone in armature.pose.bones:
            if hasattr(pose_bone, 'mmd_bone'):
                mmd_bone = pose_bone.mmd_bone
                original_j = mmd_bone.name_j
                original_e = mmd_bone.name_e
                
                if original_e:
                    mmd_bone.name_j = original_e
                    mmd_bone.name_e = original_j
                    pose_bone.name = original_e  # 更新骨骼显示名称
        
        # 切换回OBJECT模式
        bpy.ops.object.mode_set(mode='OBJECT')

    # 3. 交换顶点变形的日文和英文名称
    root_objects = [obj for obj in bpy.context.scene.objects if hasattr(obj, 'mmd_type') and obj.mmd_type == 'ROOT']
    for root in root_objects:
        # 遍历所有顶点变形
        for vm in root.mmd_root.vertex_morphs:
            original_j = vm.name
            original_e = vm.name_e
            
            if original_e:
                vm.name = original_e
                vm.name_e = original_j

# ------------------------------
# 操作符类
# ------------------------------
class ReverseJapaneseEnglish(bpy.types.Operator):
    """交换MMD模型中材质、骨骼和变形的日文与英文名称"""
    bl_idname = "mmd_tools_helper.reverse_japanese_english"
    bl_label = "Swap Japanese/English Names"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作
    bl_description = "Swap Japanese and English names for materials, bones and morphs"

    @classmethod
    def poll(cls, context):
        """仅当场景中存在对象时启用按钮"""
        return len(context.scene.objects) > 0

    def execute(self, context):
        try:
            main(context)
            self.report({'INFO'}, "Successfully swapped Japanese/English names!")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to swap names: {str(e)}")
            return {'CANCELLED'}

# ------------------------------
# 注册与注销函数
# ------------------------------
def register():
    bpy.utils.register_class(ReverseJapaneseEnglishPanel)
    bpy.utils.register_class(ReverseJapaneseEnglish)

def unregister():
    # 修复原代码中的类名错误（原代码注销了不存在的类）
    bpy.utils.unregister_class(ReverseJapaneseEnglishPanel)
    bpy.utils.unregister_class(ReverseJapaneseEnglish)

if __name__ == "__main__":
    register()
