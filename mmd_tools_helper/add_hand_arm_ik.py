import bpy
import math
# 依赖 mmd_tools 插件的 model 模块，需确保已安装
print("add_hand_arm_ik.py----")
try:
    from . import model
except ImportError:
    raise ImportError("请先安装 mmd_tools 插件（Blender 3.6 兼容版），否则脚本无法运行！")


class Add_MMD_Hand_Arm_IK_Panel(bpy.types.Panel):
    """为激活的MMD模型添加手臂/手部IK骨骼及约束"""
    bl_idname = "OBJECT_PT_mmd_add_hand_arm_ik"
    bl_label = "Add Hand Arm IK to MMD model"
    bl_space_type = "VIEW_3D"  # 3D视图空间（不变）
    bl_region_type = "UI"      # 关键修改：Blender 2.8+ 废弃 TOOLS 区域，改用 UI（右侧N面板）
    bl_category = "mmd_tools_helper"  # 面板分类（在N面板中显示的标签）
    bl_order = 11  # 排序（与腿部IK面板区分，避免重叠）

    def draw(self, context):
        layout = self.layout
        # 标题行（带骨骼图标）
        row = layout.row()
        row.label(text="Add hand arm IK to MMD model", icon="ARMATURE_DATA")
        # 功能按钮行
        row = layout.row()
        row.operator("object.add_hand_arm_ik", text="Add hand_arm IK to MMD model")
        # 空行占位（优化显示）
        layout.row()


def clear_IK(context):
    """清除已存在的手臂/手部IK骨骼和约束（适配3.6 API）"""
    IK_target_bones = []
    IK_target_tip_bones = []
    
    # 1. 获取并激活MMD骨架（修复active_object API）
    armature = model.findArmature(context.active_object)
    if not armature:
        raise ValueError("未找到MMD骨架，请选中MMD模型或其骨架！")
    context.view_layer.objects.active = armature  # 替代废弃的 scene.objects.active
    
    # 2. 切换到姿态模式，准备清理约束
    bpy.ops.object.mode_set(mode='POSE')
    
    # 待清理约束的骨骼列表（中英文命名）
    english_bones = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    japanese_bones = ["左ひじ", "右ひじ", "左手首", "右手首", "左中指１", "右中指１"]
    japanese_LR_bones = ["ひじ.L", "ひじ.R", "手首.L", "手首.R", "中指１.L", "中指１.R"]
    target_bones = english_bones + japanese_bones + japanese_LR_bones
    
    # 3. 收集IK约束对应的目标骨骼
    for bone_name in armature.pose.bones.keys():
        if bone_name in target_bones:
            pose_bone = armature.pose.bones[bone_name]
            # 反向遍历约束（避免删除时索引错乱）
            for constraint in reversed(pose_bone.constraints):
                if constraint.type == "IK" and constraint.target == armature and constraint.subtarget:
                    print(f"找到IK约束：{bone_name} → {constraint.subtarget}")
                    if constraint.subtarget not in IK_target_bones:
                        IK_target_bones.append(constraint.subtarget)
                    # 直接删除当前IK约束（提前清理，避免后续重复处理）
                    pose_bone.constraints.remove(constraint)
    
    # 4. 收集IK尖端骨骼（子骨骼）
    for bone_name in IK_target_bones:
        if bone_name in armature.data.bones:
            parent_bone = armature.data.bones[bone_name]
            for child_bone in parent_bone.children:
                if child_bone.name not in IK_target_tip_bones:
                    IK_target_tip_bones.append(child_bone.name)
    
    # 5. 删除IK骨骼（需切换到编辑模式）
    bones_to_delete = set(IK_target_bones + IK_target_tip_bones)
    print(f"待删除的IK骨骼：{bones_to_delete}")
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    for bone_name in bones_to_delete:
        if bone_name in edit_bones:  # 检查骨骼是否存在，避免报错
            edit_bones.remove(edit_bones[bone_name])
    
    # 6. 回到物体模式，清理完成
    bpy.ops.object.mode_set(mode='OBJECT')


def armature_diagnostic(armature):
    """骨架诊断：检查是否存在所需的手臂/手部骨骼（中英文）"""
    english_bones = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    japanese_bones = ["ひじ.L", "ひじ.R", "手首.L", "手首.R", "中指１.L", "中指１.R"]
    existing_bones = armature.data.bones.keys()
    
    # 检查英文骨骼
    english_ok = all(b in existing_bones for b in english_bones)
    # 检查日文骨骼
    japanese_ok = all(b in existing_bones for b in japanese_bones)
    
    print("\n=== MMD骨架诊断报告 ===")
    print(f"英文骨骼（elbow_L/wrist_L等）是否齐全：{'是' if english_ok else '否'}")
    if not english_ok:
        missing = [b for b in english_bones if b not in existing_bones]
        print(f"  缺失英文骨骼：{missing}")
    
    print(f"日文骨骼（左ひじ/左手首等）是否齐全：{'是' if japanese_ok else '否'}")
    if not japanese_ok:
        missing = [b for b in japanese_bones if b not in existing_bones]
        print(f"  缺失日文骨骼：{missing}")
    
    # 检查是否已存在IK骨骼
    ik_bones = ["elbow_IK_L", "elbow_IK_R", "middle1_IK_L", "middle1_IK_R"]
    existing_ik = [b for b in existing_bones if b in ik_bones]
    if existing_ik:
        print(f"\n已存在的IK骨骼：{existing_ik}（建议先清理再添加）")
    
    return english_ok or japanese_ok  # 至少一种命名齐全


def main(context):
    """核心功能：为MMD骨架添加手臂/手部IK骨骼及约束"""
    # 1. 获取并激活骨架
    armature = model.findArmature(context.active_object)
    if not armature:
        raise ValueError("未找到MMD骨架，请选中MMD模型或其骨架！")
    context.view_layer.objects.active = armature
    arm_data = armature.data
    bone_keys = arm_data.bones.keys()

    # 2. 骨架诊断：确保有必要的骨骼
    if not armature_diagnostic(armature):
        raise ValueError("该骨架缺少MMD标准的手臂/手部骨骼（如elbow_L/左ひじ、wrist_L/左手首等），无法添加IK！")

    # 3. 定义骨骼候选列表（中英文），用于匹配实际骨骼
    ELBOW_LEFT_CANDIDATES = ["elbow_L", "左ひじ", "ひじ.L"]    # 左肘
    ELBOW_RIGHT_CANDIDATES = ["elbow_R", "右ひじ", "ひじ.R"]  # 右肘
    WRIST_LEFT_CANDIDATES = ["wrist_L", "左手首", "手首.L"]   # 左手腕
    WRIST_RIGHT_CANDIDATES = ["wrist_R", "右手首", "手首.R"] # 右手腕
    MIDDLE1_LEFT_CANDIDATES = ["middle1_L", "左中指１", "中指１.L"]  # 左中指1节
    MIDDLE1_RIGHT_CANDIDATES = ["middle1_R", "右中指１", "中指１.R"]# 右中指1节

    # 4. 匹配实际骨骼（用next()避免未定义变量，加异常捕获）
    try:
        ELBOW_LEFT = next(b for b in bone_keys if b in ELBOW_LEFT_CANDIDATES)
        ELBOW_RIGHT = next(b for b in bone_keys if b in ELBOW_RIGHT_CANDIDATES)
        WRIST_LEFT = next(b for b in bone_keys if b in WRIST_LEFT_CANDIDATES)
        WRIST_RIGHT = next(b for b in bone_keys if b in WRIST_RIGHT_CANDIDATES)
        MIDDLE1_LEFT = next(b for b in bone_keys if b in MIDDLE1_LEFT_CANDIDATES)
        MIDDLE1_RIGHT = next(b for b in bone_keys if b in MIDDLE1_RIGHT_CANDIDATES)
    except StopIteration as e:
        raise ValueError(f"未找到关键骨骼：{str(e)}，请确认骨架为MMD标准命名！")

    print(f"\n匹配到的骨骼：")
    print(f"左肘：{ELBOW_LEFT} | 右肘：{ELBOW_RIGHT}")
    print(f"左手腕：{WRIST_LEFT} | 右手腕：{WRIST_RIGHT}")
    print(f"左中指1节：{MIDDLE1_LEFT} | 右中指1节：{MIDDLE1_RIGHT}")

    # 5. 计算IK骨骼长度（基于手腕骨骼长度，保持比例）
    wrist_length = arm_data.bones[WRIST_LEFT].length
    ik_bone_length = wrist_length * 2  # IK骨骼长度=手腕长度×2
    tip_bone_length = wrist_length * 0.05  # 尖端骨骼长度（微小，用于MMD兼容）

    # 6. 创建IK骨骼（编辑模式）
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    # --------------------------
    # 创建左肘IK骨（elbow_IK_L）
    # --------------------------
    bone = edit_bones.new("elbow_IK_L")
    wrist_left_edit = edit_bones[WRIST_LEFT]
    bone.head = wrist_left_edit.head
    bone.tail = wrist_left_edit.head
    bone.tail.z = wrist_left_edit.head.z - ik_bone_length  # 沿Z轴向下延伸

    # --------------------------
    # 创建右肘IK骨（elbow_IK_R）
    # --------------------------
    bone = edit_bones.new("elbow_IK_R")
    wrist_right_edit = edit_bones[WRIST_RIGHT]
    bone.head = wrist_right_edit.head
    bone.tail = wrist_right_edit.head
    bone.tail.z = wrist_right_edit.head.z - ik_bone_length

    # --------------------------
    # 创建左中指IK骨（middle1_IK_L，父级为左肘IK）
    # --------------------------
    bone = edit_bones.new("middle1_IK_L")
    middle1_left_edit = edit_bones[MIDDLE1_LEFT]
    bone.head = middle1_left_edit.head
    bone.tail = middle1_left_edit.head
    bone.tail.z = middle1_left_edit.head.z - ik_bone_length
    bone.parent = edit_bones["elbow_IK_L"]
    bone.use_connect = False  # 不自动连接父骨骼

    # --------------------------
    # 创建右中指IK骨（middle1_IK_R，父级为右肘IK）
    # --------------------------
    bone = edit_bones.new("middle1_IK_R")
    middle1_right_edit = edit_bones[MIDDLE1_RIGHT]
    bone.head = middle1_right_edit.head
    bone.tail = middle1_right_edit.head
    bone.tail.z = middle1_right_edit.head.z - ik_bone_length
    bone.parent = edit_bones["elbow_IK_R"]
    bone.use_connect = False

    # --------------------------
    # 创建IK尖端骨骼（隐藏，用于MMD兼容）
    # --------------------------
    def create_tip_bone(tip_name, parent_ik_name, offset_axis, offset_val):
        """辅助函数：创建隐藏的IK尖端骨骼"""
        if parent_ik_name not in edit_bones:
            print(f"警告：父IK骨骼{parent_ik_name}不存在，跳过尖端骨骼{tip_name}")
            return
        # 创建尖端骨骼
        parent_bone = edit_bones[parent_ik_name]
        tip_bone = edit_bones.new(tip_name)
        tip_bone.head = parent_bone.head
        tip_bone.tail = parent_bone.head
        # 应用偏移（微小长度，避免骨骼为点）
        setattr(tip_bone.tail, offset_axis, getattr(tip_bone.tail, offset_axis) + offset_val)
        tip_bone.parent = parent_bone
        tip_bone.use_connect = False
        # 切换到姿态模式，隐藏骨骼并配置MMD属性
        bpy.ops.object.mode_set(mode='POSE')
        if tip_name in armature.pose.bones:
            pose_tip = armature.pose.bones[tip_name]
            pose_tip.bone.hide = True  # 隐藏骨骼
            # 适配mmd_tools的骨骼属性
            if hasattr(pose_tip, "mmd_bone"):
                pose_tip.mmd_bone.is_visible = False
                pose_tip.mmd_bone.is_controllable = False
                pose_tip.mmd_bone.is_tip = True
        # 切回编辑模式，准备下一个骨骼
        bpy.ops.object.mode_set(mode='EDIT')

    # 批量创建4个尖端骨骼
    create_tip_bone("elbow_IK_L_t", "elbow_IK_L", "y", tip_bone_length)
    create_tip_bone("elbow_IK_R_t", "elbow_IK_R", "y", tip_bone_length)
    create_tip_bone("middle1_IK_L_t", "middle1_IK_L", "z", -tip_bone_length)
    create_tip_bone("middle1_IK_R_t", "middle1_IK_R", "z", -tip_bone_length)

    # 7. 添加IK约束（姿态模式）
    bpy.ops.object.mode_set(mode='POSE')

    # --------------------------
    # 左肘骨骼（ELBOW_LEFT）添加IK约束
    # --------------------------
    ik_const = armature.pose.bones[ELBOW_LEFT].constraints.new("IK")
    ik_const.name = "MMD_Arm_IK_L"
    ik_const.target = armature
    ik_const.subtarget = "elbow_IK_L"
    ik_const.chain_count = 2  # 链长：肘→肩（控制2节骨骼）
    ik_const.use_tail = True
    ik_const.iterations = 48  # 迭代次数（精度）

    # --------------------------
    # 右肘骨骼（ELBOW_RIGHT）添加IK约束
    # --------------------------
    ik_const = armature.pose.bones[ELBOW_RIGHT].constraints.new("IK")
    ik_const.name = "MMD_Arm_IK_R"
    ik_const.target = armature
    ik_const.subtarget = "elbow_IK_R"
    ik_const.chain_count = 2
    ik_const.use_tail = True
    ik_const.iterations = 48

    # --------------------------
    # 左手腕骨骼（WRIST_LEFT）添加IK约束
    # --------------------------
    ik_const = armature.pose.bones[WRIST_LEFT].constraints.new("IK")
    ik_const.name = "MMD_Wrist_IK_L"
    ik_const.target = armature
    ik_const.subtarget = "middle1_IK_L"
    ik_const.chain_count = 1  # 链长：手腕→中指（控制1节骨骼）
    ik_const.use_tail = True
    ik_const.iterations = 6

    # --------------------------
    # 右手腕骨骼（WRIST_RIGHT）添加IK约束
    # --------------------------
    ik_const = armature.pose.bones[WRIST_RIGHT].constraints.new("IK")
    ik_const.name = "MMD_Wrist_IK_R"
    ik_const.target = armature
    ik_const.subtarget = "middle1_IK_R"
    ik_const.chain_count = 1
    ik_const.use_tail = True
    ik_const.iterations = 6

    # 8. 适配mmd_tools的IK旋转约束属性
    if hasattr(armature.pose.bones[ELBOW_RIGHT], "mmd_bone"):
        armature.pose.bones[ELBOW_LEFT].mmd_bone.ik_rotation_constraint = 2
        armature.pose.bones[ELBOW_RIGHT].mmd_bone.ik_rotation_constraint = 2
        armature.pose.bones[WRIST_LEFT].mmd_bone.ik_rotation_constraint = 4
        armature.pose.bones[WRIST_RIGHT].mmd_bone.ik_rotation_constraint = 4

    # 9. 创建IK骨骼组（便于管理）
    if "IK" not in armature.pose.bone_groups:
        armature.pose.bone_groups.new(name="IK")
    ik_group = armature.pose.bone_groups["IK"]

    # 将所有IK骨骼加入组
    ik_bone_list = [
        "elbow_IK_L", "elbow_IK_R", "middle1_IK_L", "middle1_IK_R",
        "elbow_IK_L_t", "elbow_IK_R_t", "middle1_IK_L_t", "middle1_IK_R_t"
    ]
    for bone_name in ik_bone_list:
        if bone_name in armature.pose.bones:
            armature.pose.bones[bone_name].bone_group = ik_group

    # 10. 优化骨架显示（八面体骨骼，更清晰）
    arm_data.draw_type = 'OCTAHEDRAL'

    # 回到物体模式，完成操作
    bpy.ops.object.mode_set(mode='OBJECT')
    print("\nMMD手臂/手部IK添加完成！")


class Add_MMD_Hand_Arm_IK(bpy.types.Operator):
    """为激活的MMD模型添加手臂/手部IK骨骼及约束"""
    bl_idname = "object.add_hand_arm_ik"
    bl_label = "Add Hand Arm IK to MMD model"
    bl_options = {'REGISTER', 'UNDO'}  # 关键优化：支持撤销操作

    @classmethod
    def poll(cls, context):
        """检查是否满足运行条件：选中物体且能找到MMD骨架"""
        if not context.active_object:
            return False
        # 必须能通过mmd_tools找到骨架（排除非MMD模型）
        return model.findArmature(context.active_object) is not None

    def execute(self, context):
        """执行主逻辑：先清理旧IK，再添加新IK"""
        try:
            clear_IK(context)
            main(context)
            self.report({'INFO'}, "MMD手臂/手部IK添加成功！")
        except Exception as e:
            # 报错时显示具体原因
            self.report({'ERROR'}, f"操作失败：{str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}


# 注册/反注册函数（避免重复注册）
def register():
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK)
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK_Panel)


def unregister():
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK)
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK_Panel)


# 仅在直接运行脚本时注册（导入时不注册，避免冲突）
if __name__ == "__main__":
    register()
register()