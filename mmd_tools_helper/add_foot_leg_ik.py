import bpy
import math
print("add_foot_leg_ik------>>>>")
# 注意：原代码依赖 model 模块（通常来自 mmd_tools 插件），需确保已安装 mmd_tools
try:
    from . import model
except ImportError:
    raise ImportError("请先安装 mmd_tools 插件，否则脚本无法正常运行！")


# 注释的骨骼诊断函数（保留原逻辑，如需使用可取消注释）
# def armature_diagnostic():
#     ENGLISH_LEG_BONES = ["knee_L", "knee_R", "ankle_L", "ankle_R", "toe_L", "toe_R"]
#     JAPANESE_LEG_BONES = ["左ひざ", "右ひざ", "左足首", "右足首", "左つま先", "右つま先"]
#     IK_BONE_NAMES = ["leg IK_L", "leg IK_R", "toe IK_L", "toe IK_R", "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ"]
#     ENGLISH_OK = True
#     JAPANESE_OK = True

#     print('\n\n\n', '需要以下英文骨骼以添加IK:', '\n')
#     print(ENGLISH_LEG_BONES, '\n')
#     for b in ENGLISH_LEG_BONES:
#         if b not in bpy.context.active_object.data.bones.keys():
#             ENGLISH_OK = False
#             print('该骨骼不存在于骨架中:', '\n', b)
#     if ENGLISH_OK:
#         print('OK! 所有所需英文命名骨骼均存在（用于添加腿部IK）')

#     print('\n', '或需要以下日文骨骼以添加IK:', '\n')
#     print(JAPANESE_LEG_BONES, '\n')
#     for b in JAPANESE_LEG_BONES:
#         if b not in bpy.context.active_object.data.bones.keys():
#             JAPANESE_OK = False
#             print('该骨骼不存在于骨架中:', '\n', b)
#     if JAPANESE_OK:
#         print('OK! 所有所需日文命名骨骼均存在（用于添加腿部IK）', '\n')

#     print('\n', '已存在的IK骨骼名称', '\n')
#     for b in IK_BONE_NAMES:
#         if b in bpy.context.active_object.data.bones.keys():
#             print('该骨架似乎已存在IK骨骼，此骨骼可能是IK骨:', '\n', b)


class Add_MMD_foot_leg_IK_Panel(bpy.types.Panel):
    """为MMD模型添加脚部和腿部IK骨骼及约束"""
    bl_idname = "OBJECT_PT_mmd_add_foot_leg_ik"
    bl_label = "Add foot leg IK to MMD model"
    bl_space_type = "VIEW_3D"  # 3D视图空间（不变）
    bl_region_type = "UI"      # 关键修改：Blender 2.8+ 废弃 TOOLS，改用 UI 区域
    bl_category = "mmd_tools_helper"  # 侧边栏标签（在3D视图右侧"N"面板中）
    bl_order = 10  # 面板排序（可选，确保在侧边栏中位置合理）

    def draw(self, context):
        layout = self.layout
        # 标题行
        row = layout.row()
        row.label(text="Add leg and foot IK to MMD model", icon="ARMATURE_DATA")
        # 功能按钮行
        row = layout.row()
        row.operator("object.add_foot_leg_ik", text="Add leg and foot IK to MMD model")
        # 空行占位（优化显示）
        layout.row()


def clear_IK(context):
    """清除已存在的IK骨骼和约束（修复版本兼容）"""
    IK_target_bones = []
    IK_target_tip_bones = []
    
    # 关键修改：Blender 2.8+ 用 view_layer.objects.active 替代 scene.objects.active
    armature = model.findArmature(context.active_object)
    context.view_layer.objects.active = armature
    
    # 切换到姿态模式
    bpy.ops.object.mode_set(mode='POSE')
    
    # 待检查的腿部/脚部骨骼（中英文）
    english = ["knee_L", "knee_R", "ankle_L", "ankle_R", "toe_L", "toe_R"]
    japanese = ["左ひざ", "右ひざ", "左足首", "右足首", "左つま先", "右つま先"]
    japanese_L_R = ["ひざ.L", "ひざ.R", "足首.L", "足首.R", "つま先.L", "つま先.R"]
    leg_foot_bones = english + japanese + japanese_L_R
    
    # 收集IK目标骨骼
    for b_name in armature.pose.bones.keys():
        if b_name in leg_foot_bones:
            pose_bone = armature.pose.bones[b_name]
            for constraint in pose_bone.constraints:
                if constraint.type == "IK":
                    print("IK约束目标:", constraint.target)
                    if constraint.target == armature and constraint.subtarget:
                        print("IK约束子目标:", constraint.subtarget)
                        if constraint.subtarget not in IK_target_bones:
                            IK_target_bones.append(constraint.subtarget)
    
    # 收集IK尖端骨骼
    for b_name in IK_target_bones:
        if b_name in armature.data.bones:
            bone = armature.data.bones[b_name]
            for child in bone.children:
                if child.name not in IK_target_tip_bones:
                    IK_target_tip_bones.append(child.name)
    
    # 删除IK骨骼（需切换到编辑模式）
    bones_to_delete = set(IK_target_bones + IK_target_tip_bones)
    print("待删除的IK骨骼:", bones_to_delete)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    for b_name in bones_to_delete:
        if b_name in edit_bones:
            edit_bones.remove(edit_bones[b_name])
    
    # 删除IK约束（返回姿态模式）
    bpy.ops.object.mode_set(mode='POSE')
    for b_name in leg_foot_bones:
        if b_name in armature.pose.bones:
            pose_bone = armature.pose.bones[b_name]
            # 反向遍历约束列表（避免删除时索引错乱）
            for constraint in reversed(pose_bone.constraints):
                pose_bone.constraints.remove(constraint)
    
    # 回到物体模式
    bpy.ops.object.mode_set(mode='OBJECT')


def main(context):
    """核心功能：为MMD骨架添加IK骨骼和约束"""
    # 获取并激活MMD骨架
    armature = model.findArmature(context.active_object)
    context.view_layer.objects.active = armature
    armature_data = armature.data
    bone_keys = armature_data.bones.keys()

    # 检查骨骼命名类型（英文/日文）
    english_bones = all(e in bone_keys for e in ["knee_L", "knee_R", "ankle_L", "ankle_R", "toe_L", "toe_R"])
    japanese_bones = all(j in bone_keys for j in ["左ひざ", "右ひざ", "左足首", "右足首", "左つま先", "右つま先"])
    japanese_L_R = all(j in bone_keys for j in ["ひざ.L", "ひざ.R", "足首.L", "足首.R", "つま先.L", "つま先.R"])

    print('英文骨骼存在:', english_bones)
    print('日文骨骼存在:', japanese_bones)
    print('日文.L/R骨骼存在:', japanese_L_R)
    print('\n')

    # 断言：确保是MMD骨架（无对应骨骼则报错）
    assert (english_bones or japanese_bones or japanese_L_R), \
        "这不是MMD骨架！脚本需要MMD标准的膝盖/脚踝/脚趾骨骼名称才能运行。"

    # 检查是否已存在IK骨骼
    IK_BONE_NAMES = ["leg IK_L", "leg IK_R", "toe IK_L", "toe_R", 
                     "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ",
                     "足ＩＫ.L", "足ＩＫ.R", "つま先ＩＫ.L", "つま先ＩＫ.R"]
    has_ik_bones = any(ik in bone_keys for ik in IK_BONE_NAMES)
    assert not has_ik_bones, "该骨架已存在MMD IK骨骼，请先清除再添加！"

    # 定义IK骨骼名称（根据骨骼类型选择中英文）
    if english_bones:
        LEG_IK_LEFT = "leg IK_L"
        LEG_IK_RIGHT = "leg IK_R"
        TOE_IK_LEFT = "toe IK_L"
        TOE_IK_RIGHT = "toe IK_R"
        LEG_IK_LEFT_TIP = "leg IK_L_t"
        LEG_IK_RIGHT_TIP = "leg IK_R_t"
        TOE_IK_LEFT_TIP = "toe IK_L_t"
        TOE_IK_RIGHT_TIP = "toe IK_R_t"
        ROOT_BONE = "root"
    else:  # 日文骨骼（含.L/R格式）
        LEG_IK_LEFT = "左足ＩＫ"
        LEG_IK_RIGHT = "右足ＩＫ"
        TOE_IK_LEFT = "左つま先ＩＫ"
        TOE_IK_RIGHT = "右つま先ＩＫ"
        LEG_IK_LEFT_TIP = "左足ＩＫ先"
        LEG_IK_RIGHT_TIP = "右足ＩＫ先"
        TOE_IK_LEFT_TIP = "左つま先ＩＫ先"
        TOE_IK_RIGHT_TIP = "右つま先ＩＫ先"
        ROOT_BONE = "全ての親"

    # 骨骼名称列表（用于匹配实际骨骼）
    KNEE_LEFT_CANDIDATES = ["knee_L", "左ひざ", "ひざ.L"]
    KNEE_RIGHT_CANDIDATES = ["knee_R", "右ひざ", "ひざ.R"]
    ANKLE_LEFT_CANDIDATES = ["ankle_L", "左足首", "足首.L"]
    ANKLE_RIGHT_CANDIDATES = ["ankle_R", "右足首", "足首.R"]
    TOE_LEFT_CANDIDATES = ["toe_L", "左つま先", "つま先.L"]
    TOE_RIGHT_CANDIDATES = ["toe_R", "右つま先", "つま先.R"]

    # 匹配实际骨骼名称
    KNEE_LEFT = next(b for b in bone_keys if b in KNEE_LEFT_CANDIDATES)
    KNEE_RIGHT = next(b for b in bone_keys if b in KNEE_RIGHT_CANDIDATES)
    ANKLE_LEFT = next(b for b in bone_keys if b in ANKLE_LEFT_CANDIDATES)
    ANKLE_RIGHT = next(b for b in bone_keys if b in ANKLE_RIGHT_CANDIDATES)
    TOE_LEFT = next(b for b in bone_keys if b in TOE_LEFT_CANDIDATES)
    TOE_RIGHT = next(b for b in bone_keys if b in TOE_RIGHT_CANDIDATES)

    print('匹配到的骨骼:')
    print(f'左膝盖: {KNEE_LEFT}, 右膝盖: {KNEE_RIGHT}')
    print(f'左脚踝: {ANKLE_LEFT}, 右脚踝: {ANKLE_RIGHT}')
    print(f'左脚趾: {TOE_LEFT}, 右脚趾: {TOE_RIGHT}\n')

    # 1. 配置膝盖IK旋转限制（姿态模式）
    bpy.ops.object.mode_set(mode='POSE')
    armature.pose.bones[KNEE_LEFT].use_ik_limit_x = True
    armature.pose.bones[KNEE_RIGHT].use_ik_limit_x = True

    # 计算骨骼长度（用于IK骨骼尺寸）
    foot_bone_length = armature_data.bones[ANKLE_LEFT].length
    half_foot_length = foot_bone_length * 0.5
    tiny_length = foot_bone_length * 0.05  # IK尖端骨骼长度

    # 2. 创建IK骨骼（编辑模式）
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature_data.edit_bones
    root_bone = edit_bones.get(ROOT_BONE)  # 根骨骼（可能不存在）

    # 创建左腿IK骨
    bone = edit_bones.new(LEG_IK_LEFT)
    ankle_left = edit_bones[ANKLE_LEFT]
    bone.head = ankle_left.head
    bone.tail = ankle_left.head
    bone.tail.y = ankle_left.head.y + foot_bone_length  # 沿Y轴延伸
    if root_bone:
        bone.parent = root_bone

    # 创建右腿IK骨
    bone = edit_bones.new(LEG_IK_RIGHT)
    ankle_right = edit_bones[ANKLE_RIGHT]
    bone.head = ankle_right.head
    bone.tail = ankle_right.head
    bone.tail.y = ankle_right.head.y + foot_bone_length
    if root_bone:
        bone.parent = root_bone

    # 创建左脚趾IK骨
    bone = edit_bones.new(TOE_IK_LEFT)
    toe_left = edit_bones[TOE_LEFT]
    bone.head = toe_left.head
    bone.tail = toe_left.head
    bone.tail.z = toe_left.head.z - half_foot_length  # 沿Z轴向下
    bone.parent = edit_bones[LEG_IK_LEFT]
    bone.use_connect = False

    # 创建右脚趾IK骨
    bone = edit_bones.new(TOE_IK_RIGHT)
    toe_right = edit_bones[TOE_RIGHT]
    bone.head = toe_right.head
    bone.tail = toe_right.head
    bone.tail.z = toe_right.head.z - half_foot_length
    bone.parent = edit_bones[LEG_IK_RIGHT]
    bone.use_connect = False

    # 创建IK尖端骨骼（隐藏，用于MMD兼容）
    def create_tip_bone(name, parent_name, offset_axis, offset_value):
        """辅助函数：创建IK尖端骨骼"""
        if parent_name not in edit_bones:
            return
        parent_bone = edit_bones[parent_name]
        bone = edit_bones.new(name)
        bone.head = parent_bone.head
        bone.tail = parent_bone.head
        # 应用偏移（根据轴方向）
        setattr(bone.tail, offset_axis, getattr(bone.tail, offset_axis) + offset_value)
        bone.parent = parent_bone
        bone.use_connect = False
        # 切换到姿态模式隐藏骨骼
        bpy.ops.object.mode_set(mode='POSE')
        if name in armature.pose.bones:
            pose_bone = armature.pose.bones[name]
            pose_bone.bone.hide = True  # 隐藏骨骼
            # 配置MMD骨骼属性（mmd_tools兼容）
            if hasattr(pose_bone, "mmd_bone"):
                pose_bone.mmd_bone.is_visible = False
                pose_bone.mmd_bone.is_controllable = False
                pose_bone.mmd_bone.is_tip = True
        # 切回编辑模式
        bpy.ops.object.mode_set(mode='EDIT')

    # 创建所有尖端骨骼
    create_tip_bone(LEG_IK_LEFT_TIP, LEG_IK_LEFT, "y", tiny_length)
    create_tip_bone(LEG_IK_RIGHT_TIP, LEG_IK_RIGHT, "y", tiny_length)
    create_tip_bone(TOE_IK_LEFT_TIP, TOE_IK_LEFT, "z", -tiny_length)
    create_tip_bone(TOE_IK_RIGHT_TIP, TOE_IK_RIGHT, "z", -tiny_length)

    # 3. 添加IK约束和旋转限制（姿态模式）
    bpy.ops.object.mode_set(mode='POSE')

    # --------------------------
    # 左膝盖IK约束
    # --------------------------
    ik_const = armature.pose.bones[KNEE_LEFT].constraints.new("IK")
    ik_const.target = armature
    ik_const.subtarget = LEG_IK_LEFT
    ik_const.chain_count = 2  # 链长：膝盖→大腿
    ik_const.use_tail = True
    ik_const.iterations = 48  # 迭代次数（精度）

    # 左膝盖旋转限制
    rot_limit = armature.pose.bones[KNEE_LEFT].constraints.new("LIMIT_ROTATION")
    rot_limit.name = "mmd_ik_limit_override"
    rot_limit.use_limit_x = True
    rot_limit.use_limit_y = True
    rot_limit.use_limit_z = True
    rot_limit.min_x = math.pi / 360  # 0.5度（最小旋转）
    rot_limit.max_x = math.pi        # 180度（最大旋转）
    rot_limit.min_y = rot_limit.max_y = 0
    rot_limit.min_z = rot_limit.max_z = 0
    rot_limit.owner_space = "POSE"

    # --------------------------
    # 右膝盖IK约束（与左膝盖对称）
    # --------------------------
    ik_const = armature.pose.bones[KNEE_RIGHT].constraints.new("IK")
    ik_const.target = armature
    ik_const.subtarget = LEG_IK_RIGHT
    ik_const.chain_count = 2
    ik_const.use_tail = True
    ik_const.iterations = 48

    rot_limit = armature.pose.bones[KNEE_RIGHT].constraints.new("LIMIT_ROTATION")
    rot_limit.name = "mmd_ik_limit_override"
    rot_limit.use_limit_x = True
    rot_limit.use_limit_y = True
    rot_limit.use_limit_z = True
    rot_limit.min_x = math.pi / 360
    rot_limit.max_x = math.pi
    rot_limit.min_y = rot_limit.max_y = 0
    rot_limit.min_z = rot_limit.max_z = 0
    rot_limit.owner_space = "POSE"

    # --------------------------
    # 左脚踝IK约束（控制脚趾）
    # --------------------------
    ik_const = armature.pose.bones[ANKLE_LEFT].constraints.new("IK")
    ik_const.target = armature
    ik_const.subtarget = TOE_IK_LEFT
    ik_const.chain_count = 1  # 链长：脚踝→脚趾
    ik_const.use_tail = True
    ik_const.iterations = 6

    # --------------------------
    # 右脚踝IK约束（与左脚踝对称）
    # --------------------------
    ik_const = armature.pose.bones[ANKLE_RIGHT].constraints.new("IK")
    ik_const.target = armature
    ik_const.subtarget = TOE_IK_RIGHT
    ik_const.chain_count = 1
    ik_const.use_tail = True
    ik_const.iterations = 6

    # 4. 配置MMD骨骼属性（mmd_tools兼容）
    if hasattr(armature.pose.bones[KNEE_RIGHT], "mmd_bone"):
        armature.pose.bones[KNEE_RIGHT].mmd_bone.ik_rotation_constraint = 2
        armature.pose.bones[KNEE_LEFT].mmd_bone.ik_rotation_constraint = 2
        armature.pose.bones[ANKLE_RIGHT].mmd_bone.ik_rotation_constraint = 4
        armature.pose.bones[ANKLE_LEFT].mmd_bone.ik_rotation_constraint = 4

    # 5. 创建IK骨骼组（便于管理）
    if "IK" not in armature.pose.bone_groups:
        armature.pose.bone_groups.new(name="IK")
    ik_group = armature.pose.bone_groups["IK"]

    # 将IK骨骼加入组
    for bone_name in [LEG_IK_LEFT, LEG_IK_RIGHT, TOE_IK_LEFT, TOE_IK_RIGHT,
                      LEG_IK_LEFT_TIP, LEG_IK_RIGHT_TIP, TOE_IK_LEFT_TIP, TOE_IK_RIGHT_TIP]:
        if bone_name in armature.pose.bones:
            armature.pose.bones[bone_name].bone_group = ik_group

    # 6. 优化骨架显示（八面体骨骼显示）
    armature_data.draw_type = 'OCTAHEDRAL'

    # 回到物体模式
    bpy.ops.object.mode_set(mode='OBJECT')


class Add_MMD_foot_leg_IK(bpy.types.Operator):
    """为MMD模型添加脚部和腿部IK骨骼及约束的操作器"""
    bl_idname = "object.add_foot_leg_ik"
    bl_label = "Add foot leg IK to MMD model"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销（优化用户体验）

    @classmethod
    def poll(cls, context):
        """检查是否满足运行条件：选中物体且为MMD相关"""
        if not context.active_object:
            return False
        # 允许选中模型网格或骨架（通过mmd_tools查找骨架）
        return model.findArmature(context.active_object) is not None

    def execute(self, context):
        """执行主逻辑：先清除旧IK，再添加新IK"""
        try:
            clear_IK(context)
            main(context)
            self.report({'INFO'}, "MMD腿部/脚部IK添加成功！")
        except Exception as e:
            self.report({'ERROR'}, f"执行失败：{str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}


# 注册/反注册函数（修复重复注册问题）
def register():
    """注册Blender插件类"""
    bpy.utils.register_class(Add_MMD_foot_leg_IK)
    bpy.utils.register_class(Add_MMD_foot_leg_IK_Panel)


def unregister():
    """反注册Blender插件类（卸载时调用）"""
    bpy.utils.unregister_class(Add_MMD_foot_leg_IK)
    bpy.utils.unregister_class(Add_MMD_foot_leg_IK_Panel)


# 仅在直接运行脚本时注册（避免导入时重复注册）
if __name__ == "__main__":
    register()
register()