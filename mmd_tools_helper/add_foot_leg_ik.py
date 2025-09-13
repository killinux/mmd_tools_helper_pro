import bpy
import math
from . import model

print("add_foot_leg_ik-->")

# ------------------------------
# 核心修复：通用骨骼隐藏函数
# ------------------------------
def hide_bone(bone, hide=True):
    """
    兼容所有 Blender 版本的骨骼隐藏函数
    通过检测骨骼对象实际拥有的属性来选择正确的隐藏方式
    """
    if hasattr(bone, "hide_viewport"):
        # Blender 2.8+ 版本：分离控制显示和选择状态
        bone.hide_viewport = hide  # 视图中隐藏
        bone.hide_select = hide    # 禁止选择
    else:
        # Blender 2.79 及以下版本：单一属性控制
        bone.hide = hide


# ------------------------------
# UI 面板类
# ------------------------------
class Add_MMD_foot_leg_IK_Panel(bpy.types.Panel):
    """为 MMD 模型添加腿脚 IK 骨骼和约束的面板"""
    bl_idname = "OBJECT_PT_mmd_add_foot_leg_ik"
    bl_label = "Add foot leg IK to MMD model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        view_layer = context.view_layer
        
        # 面板标题
        row = layout.row()
        row.label(text="Add leg and foot IK to MMD model", icon="ARMATURE_DATA")
        
        # 添加 IK 按钮（仅选中对象时可用）
        row = layout.row()
        op = row.operator("object.add_foot_leg_ik", text="Add leg and foot IK to MMD model")
        row.enabled = bool(view_layer.objects.active)


# ------------------------------
# 清除现有 IK 骨骼和约束
# ------------------------------
def clear_IK(context):
    IK_target_bones = []
    IK_target_tip_bones = []
    view_layer = context.view_layer
    
    # 获取骨架对象
    armature_obj = model.findArmature(context.active_object)
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return
    view_layer.objects.active = armature_obj

    # 切换到姿态模式
    try:
        bpy.ops.object.mode_set(mode='POSE')
    except RuntimeError:
        return

    # 定义需要检查的腿脚骨骼（多语言支持）
    english = ["knee_L", "knee_R", "ankle_L", "ankle_R", "toe_L", "toe_R"]
    japanese = ["左ひざ", "右ひざ", "左足首", "右足首", "左つま先", "右つま先"]
    japanese_L_R = ["ひざ.L", "ひざ.R", "足首.L", "足首.R", "つま先.L", "つま先.R"]
    leg_foot_bones = english + japanese + japanese_L_R

    # 收集 IK 目标骨骼
    for bone_name in armature_obj.pose.bones.keys():
        if bone_name in leg_foot_bones:
            pose_bone = armature_obj.pose.bones[bone_name]
            for constraint in pose_bone.constraints:
                if constraint.type == "IK" and constraint.target == armature_obj:
                    if constraint.subtarget and constraint.subtarget not in IK_target_bones:
                        IK_target_bones.append(constraint.subtarget)

    # 收集 IK 尖端骨骼
    for bone_name in IK_target_bones:
        if bone_name in armature_obj.data.bones:
            for child in armature_obj.data.bones[bone_name].children:
                if child.name not in IK_target_tip_bones:
                    IK_target_tip_bones.append(child.name)

    # 删除 IK 骨骼
    bones_to_delete = set(IK_target_bones + IK_target_tip_bones)
    if bones_to_delete:
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = armature_obj.data.edit_bones
            for bone_name in bones_to_delete:
                if bone_name in edit_bones:
                    edit_bones.remove(edit_bones[bone_name])
        except RuntimeError:
            pass

    # 删除约束
    try:
        bpy.ops.object.mode_set(mode='POSE')
        for bone_name in leg_foot_bones:
            if bone_name in armature_obj.pose.bones:
                pose_bone = armature_obj.pose.bones[bone_name]
                while pose_bone.constraints:
                    pose_bone.constraints.remove(pose_bone.constraints[0])
    except RuntimeError:
        pass

    # 回到物体模式
    bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------
# 核心逻辑：创建腿脚 IK
# ------------------------------
def main(context):
    view_layer = context.view_layer
    armature_obj = model.findArmature(context.active_object)
    
    # 验证骨架对象
    if not armature_obj or armature_obj.type != 'ARMATURE':
        raise Exception("未找到有效的 MMD 骨架对象")
    view_layer.objects.active = armature_obj

    # 定义骨骼名称列表（多语言支持）
    english = ["knee_L", "knee_R", "ankle_L", "ankle_R", "toe_L", "toe_R"]
    japanese = ["左ひざ", "右ひざ", "左足首", "右足首", "左つま先", "右つま先"]
    japanese_L_R = ["ひざ.L", "ひざ.R", "足首.L", "足首.R", "つま先.L", "つま先.R"]
    bone_keys = armature_obj.data.bones.keys()

    # 检测骨骼语言类型
    has_english = all(b in bone_keys for b in english)
    has_japanese = all(b in bone_keys for b in japanese)
    has_japanese_L_R = all(b in bone_keys for b in japanese_L_R)

    if not (has_english or has_japanese or has_japanese_L_R):
        raise Exception("未找到必要的膝盖、脚踝或脚趾骨骼，无法添加 IK")

    # 检测已有 IK 骨骼（避免重复创建）
    existing_ik_bones = [
        "leg IK_L", "leg IK_R", "toe IK_L", "toe IK_R",
        "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ",
        "足ＩＫ.L", "足ＩＫ.R", "つま先ＩＫ.L", "つま先ＩＫ.R"
    ]
    if any(b in bone_keys for b in existing_ik_bones):
        raise Exception("骨架已包含 IK 骨骼，请先清除")

    # 设置 IK 骨骼名称（根据语言类型）
    if has_english:
        LEG_IK_LEFT_BONE = "leg IK_L"
        LEG_IK_RIGHT_BONE = "leg IK_R"
        TOE_IK_LEFT_BONE = "toe IK_L"
        TOE_IK_RIGHT_BONE = "toe IK_R"
        LEG_IK_LEFT_BONE_TIP = "leg IK_L_t"
        LEG_IK_RIGHT_BONE_TIP = "leg IK_R_t"
        TOE_IK_LEFT_BONE_TIP = "toe IK_L_t"
        TOE_IK_RIGHT_BONE_TIP = "toe IK_R_t"
        ROOT_BONE = "root"
    else:
        LEG_IK_LEFT_BONE = "左足ＩＫ"
        LEG_IK_RIGHT_BONE = "右足ＩＫ"
        TOE_IK_LEFT_BONE = "左つま先ＩＫ"
        TOE_IK_RIGHT_BONE = "右つま先ＩＫ"
        LEG_IK_LEFT_BONE_TIP = "左足ＩＫ先"
        LEG_IK_RIGHT_BONE_TIP = "右足ＩＫ先"
        TOE_IK_LEFT_BONE_TIP = "左つま先ＩＫ先"
        TOE_IK_RIGHT_BONE_TIP = "右つま先ＩＫ先"
        ROOT_BONE = "全ての親"

    # 查找关键骨骼（多语言匹配）
    KNEE_LEFT = next((b for b in ["knee_L", "左ひざ", "ひざ.L"] if b in bone_keys), None)
    KNEE_RIGHT = next((b for b in ["knee_R", "右ひざ", "ひざ.R"] if b in bone_keys), None)
    ANKLE_LEFT = next((b for b in ["ankle_L", "左足首", "足首.L"] if b in bone_keys), None)
    ANKLE_RIGHT = next((b for b in ["ankle_R", "右足首", "足首.R"] if b in bone_keys), None)
    TOE_LEFT = next((b for b in ["toe_L", "左つま先", "つま先.L"] if b in bone_keys), None)
    TOE_RIGHT = next((b for b in ["toe_R", "右つま先", "つま先.R"] if b in bone_keys), None)

    if None in [KNEE_LEFT, KNEE_RIGHT, ANKLE_LEFT, ANKLE_RIGHT, TOE_LEFT, TOE_RIGHT]:
        raise Exception("缺少必要的骨骼，请检查模型完整性")

    # 设置膝盖 IK 限制
    try:
        bpy.ops.object.mode_set(mode='POSE')
        armature_obj.pose.bones[KNEE_LEFT].use_ik_limit_x = True
        armature_obj.pose.bones[KNEE_RIGHT].use_ik_limit_x = True
    except RuntimeError as e:
        raise Exception(f"无法设置膝盖 IK 限制: {str(e)}")

    # 计算骨骼长度（基于脚踝骨骼）
    ankle_bone = armature_obj.data.bones[ANKLE_LEFT]
    LENGTH = ankle_bone.length
    HALF_LENGTH = LENGTH * 0.5
    TIP_LENGTH = LENGTH * 0.05  # 尖端骨骼长度

    # 创建 IK 骨骼
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = armature_obj.data.edit_bones
        root_bone = edit_bones.get(ROOT_BONE)

        # 左腿 IK 骨骼
        bone = edit_bones.new(LEG_IK_LEFT_BONE)
        bone.head = edit_bones[ANKLE_LEFT].head
        bone.tail = bone.head.copy()
        bone.tail.y += LENGTH
        if root_bone:
            bone.parent = root_bone

        # 左腿 IK 尖端骨骼
        tip = edit_bones.new(LEG_IK_LEFT_BONE_TIP)
        tip.head = bone.head
        tip.tail = tip.head.copy()
        tip.tail.y += TIP_LENGTH
        tip.parent = bone
        tip.use_connect = False

        # 右腿 IK 骨骼
        bone = edit_bones.new(LEG_IK_RIGHT_BONE)
        bone.head = edit_bones[ANKLE_RIGHT].head
        bone.tail = bone.head.copy()
        bone.tail.y += LENGTH
        if root_bone:
            bone.parent = root_bone

        # 右腿 IK 尖端骨骼
        tip = edit_bones.new(LEG_IK_RIGHT_BONE_TIP)
        tip.head = bone.head
        tip.tail = tip.head.copy()
        tip.tail.y += TIP_LENGTH
        tip.parent = bone
        tip.use_connect = False

        # 左脚趾 IK 骨骼
        bone = edit_bones.new(TOE_IK_LEFT_BONE)
        bone.head = edit_bones[TOE_LEFT].head
        bone.tail = bone.head.copy()
        bone.tail.z -= HALF_LENGTH
        bone.parent = edit_bones[LEG_IK_LEFT_BONE]
        bone.use_connect = False

        # 左脚趾 IK 尖端骨骼
        tip = edit_bones.new(TOE_IK_LEFT_BONE_TIP)
        tip.head = bone.head
        tip.tail = tip.head.copy()
        tip.tail.z -= TIP_LENGTH
        tip.parent = bone
        tip.use_connect = False

        # 右脚趾 IK 骨骼
        bone = edit_bones.new(TOE_IK_RIGHT_BONE)
        bone.head = edit_bones[TOE_RIGHT].head
        bone.tail = bone.head.copy()
        bone.tail.z -= HALF_LENGTH
        bone.parent = edit_bones[LEG_IK_RIGHT_BONE]
        bone.use_connect = False

        # 右脚趾 IK 尖端骨骼
        tip = edit_bones.new(TOE_IK_RIGHT_BONE_TIP)
        tip.head = bone.head
        tip.tail = tip.head.copy()
        tip.tail.z -= TIP_LENGTH
        tip.parent = bone
        tip.use_connect = False

    except RuntimeError as e:
        raise Exception(f"创建 IK 骨骼失败: {str(e)}")

    # 隐藏尖端骨骼（使用通用隐藏函数，核心修复）
    try:
        bpy.ops.object.mode_set(mode='POSE')
        tip_bones = [
            LEG_IK_LEFT_BONE_TIP, LEG_IK_RIGHT_BONE_TIP,
            TOE_IK_LEFT_BONE_TIP, TOE_IK_RIGHT_BONE_TIP
        ]
        for tip_name in tip_bones:
            if tip_name in armature_obj.pose.bones:
                pose_bone = armature_obj.pose.bones[tip_name]
                # 使用通用隐藏函数，自动适配所有Blender版本
                hide_bone(pose_bone.bone, True)
                
                # MMD 骨骼属性（如果存在）
                if hasattr(pose_bone, "mmd_bone"):
                    pose_bone.mmd_bone.is_visible = False
                    pose_bone.mmd_bone.is_controllable = False
                    pose_bone.mmd_bone.is_tip = True
    except RuntimeError as e:
        raise Exception(f"隐藏尖端骨骼失败：{str(e)}")

    # 添加 IK 约束
    try:
        # 左膝盖 IK 约束
        ik = armature_obj.pose.bones[KNEE_LEFT].constraints.new("IK")
        ik.target = armature_obj
        ik.subtarget = LEG_IK_LEFT_BONE
        ik.chain_count = 2
        ik.use_tail = True
        ik.iterations = 48

        # 左膝盖旋转限制
        limit = armature_obj.pose.bones[KNEE_LEFT].constraints.new("LIMIT_ROTATION")
        limit.name = "mmd_ik_limit_override"
        limit.use_limit_x = True
        limit.min_x = math.pi / 360  # 0.5度
        limit.max_x = math.pi        # 180度
        limit.owner_space = "POSE"

        # 右膝盖 IK 约束
        ik = armature_obj.pose.bones[KNEE_RIGHT].constraints.new("IK")
        ik.target = armature_obj
        ik.subtarget = LEG_IK_RIGHT_BONE
        ik.chain_count = 2
        ik.use_tail = True
        ik.iterations = 48

        # 右膝盖旋转限制
        limit = armature_obj.pose.bones[KNEE_RIGHT].constraints.new("LIMIT_ROTATION")
        limit.name = "mmd_ik_limit_override"
        limit.use_limit_x = True
        limit.min_x = math.pi / 360
        limit.max_x = math.pi
        limit.owner_space = "POSE"

        # 左脚踝 IK 约束
        ik = armature_obj.pose.bones[ANKLE_LEFT].constraints.new("IK")
        ik.target = armature_obj
        ik.subtarget = TOE_IK_LEFT_BONE
        ik.chain_count = 1
        ik.iterations = 6

        # 右脚踝 IK 约束
        ik = armature_obj.pose.bones[ANKLE_RIGHT].constraints.new("IK")
        ik.target = armature_obj
        ik.subtarget = TOE_IK_RIGHT_BONE
        ik.chain_count = 1
        ik.iterations = 6

    except Exception as e:
        raise Exception(f"添加 IK 约束失败: {str(e)}")

    # 设置 MMD 骨骼属性（如果安装了 mmd_tools）
    if hasattr(armature_obj.pose.bones[KNEE_RIGHT], "mmd_bone"):
        armature_obj.pose.bones[KNEE_LEFT].mmd_bone.ik_rotation_constraint = 2
        armature_obj.pose.bones[KNEE_RIGHT].mmd_bone.ik_rotation_constraint = 2
        armature_obj.pose.bones[ANKLE_LEFT].mmd_bone.ik_rotation_constraint = 4
        armature_obj.pose.bones[ANKLE_RIGHT].mmd_bone.ik_rotation_constraint = 4

    # 创建 IK 骨骼组
    if "IK" not in armature_obj.pose.bone_groups:
        armature_obj.pose.bone_groups.new(name="IK")

    # 添加骨骼到组
    ik_bones = [
        LEG_IK_LEFT_BONE, LEG_IK_RIGHT_BONE,
        TOE_IK_LEFT_BONE, TOE_IK_RIGHT_BONE,
        LEG_IK_LEFT_BONE_TIP, LEG_IK_RIGHT_BONE_TIP,
        TOE_IK_LEFT_BONE_TIP, TOE_IK_RIGHT_BONE_TIP
    ]
    for bone_name in ik_bones:
        if bone_name in armature_obj.pose.bones:
            armature_obj.pose.bones[bone_name].bone_group = armature_obj.pose.bone_groups["IK"]

    # 设置骨架显示类型
    if hasattr(armature_obj.data, "display_type"):
        armature_obj.data.display_type = 'OCTAHEDRAL'
    else:
        armature_obj.data.draw_type = 'OCTAHEDRAL'

    # 回到物体模式
    bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------
# 操作器类：执行添加 IK 操作
# ------------------------------
class Add_MMD_foot_leg_IK(bpy.types.Operator):
    """为 MMD 模型添加腿脚 IK 骨骼和约束"""
    bl_idname = "object.add_foot_leg_ik"
    bl_label = "Add foot leg IK to MMD model"
    bl_options = {"REGISTER", "UNDO"}  # 支持撤销

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        try:
            clear_IK(context)  # 先清除现有 IK
            main(context)      # 执行 IK 创建
            self.report({"INFO"}, "成功添加腿脚 IK")
            return {'FINISHED'}
        except Exception as e:
            self.report({"ERROR"}, f"添加 IK 失败：{str(e)}")
            return {'CANCELLED'}


# ------------------------------
# 插件注册/注销
# ------------------------------
def register():
    bpy.utils.register_class(Add_MMD_foot_leg_IK)
    bpy.utils.register_class(Add_MMD_foot_leg_IK_Panel)
    print("MMD 腿脚 IK 工具注册成功")


def unregister():
    bpy.utils.unregister_class(Add_MMD_foot_leg_IK)
    bpy.utils.unregister_class(Add_MMD_foot_leg_IK_Panel)
    print("MMD 腿脚 IK 工具注销成功")


if __name__ == "__main__":
    register()
