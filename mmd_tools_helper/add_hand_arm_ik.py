import bpy
import math
from . import model  # 需确保同目录下有 model.py（含 findArmature 函数）


# ------------------------------
# 1. 通用工具函数：骨骼隐藏（适配 Blender 2.8+）
# ------------------------------
def hide_bone(bone, hide=True):
    """
    隐藏骨骼（适配 Blender 3.6）
    - hide_viewport：控制视图中显示/隐藏
    - hide_select：控制是否可选中（避免误操作）
    """
    if hasattr(bone, "hide_viewport"):
        bone.hide_viewport = hide
        bone.hide_select = hide
    else:
        # 兼容旧版本（实际 Blender 3.6 无需此分支）
        bone.hide = hide


# ------------------------------
# 2. UI 面板类（适配 Blender 2.8+ 侧边栏）
# ------------------------------
class Add_MMD_Hand_Arm_IK_Panel(bpy.types.Panel):
    """为 MMD 模型添加手臂/手部 IK 骨骼和约束的面板"""
    bl_idname = "OBJECT_PT_mmd_add_hand_arm_ik"
    bl_label = "Add Hand Arm IK to MMD model"
    bl_space_type = "VIEW_3D"  # 所在空间：3D 视图
    bl_region_type = "UI"      # 所在区域：侧边栏（废弃旧 TOOLS 区域）
    bl_category = "mmd_tools_helper"  # 侧边栏标签（无则手动创建）
    bl_context = "objectmode"  # 仅物体模式显示（避免编辑模式报错）

    def draw(self, context):
        layout = self.layout
        view_layer = context.scene.view_layers[0]  # 从视图层获取活跃对象

        # 标题与图标
        row = layout.row()
        row.label(text="Add hand arm IK to MMD model", icon="ARMATURE_DATA")
        
        # 空行分隔
        layout.separator()

        # 添加 IK 按钮（仅选中对象时可点击）
        row = layout.row()
        row.operator("object.add_hand_arm_ik", text="Add hand_arm IK to MMD model")
        row.enabled = bool(view_layer.objects.active)  # 控制按钮可用性


# ------------------------------
# 3. 辅助函数：清除现有手臂/手部 IK 骨骼和约束
# ------------------------------
def clear_IK(context):
    scene = context.scene
    view_layer = scene.view_layers[0]
    IK_target_bones = []
    IK_target_tip_bones = []

    # 1. 找到并激活骨架对象
    active_obj = view_layer.objects.active
    armature_obj = model.findArmature(active_obj)
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("【清除 IK】未找到有效骨架对象，跳过清除")
        return
    view_layer.objects.active = armature_obj  # 激活骨架

    # 2. 切换到姿态模式，收集需删除的 IK 目标骨骼
    try:
        bpy.ops.object.mode_set(mode='POSE')
    except RuntimeError:
        print("【清除 IK】无法切换到姿态模式，跳过清除")
        return

    # 定义需检查的手臂/手部骨骼（英文/日文/L.R 后缀）
    english = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    japanese = ["左ひじ", "右ひじ", "左手首", "右手首", "左中指１", "右中指１"]
    japanese_L_R = ["ひじ.L", "ひじ.R", "手首.L", "手首.R", "中指１.L", "中指１.R"]
    arm_hand_bones = english + japanese + japanese_L_R

    # 收集 IK 约束的目标骨骼
    for bone_name in armature_obj.pose.bones.keys():
        if bone_name in arm_hand_bones:
            pose_bone = armature_obj.pose.bones[bone_name]
            for constraint in pose_bone.constraints:
                if constraint.type == "IK" and constraint.target == armature_obj:
                    subtarget = constraint.subtarget
                    if subtarget and subtarget not in IK_target_bones:
                        IK_target_bones.append(subtarget)
                        print(f"【清除 IK】找到 IK 目标骨骼：{subtarget}")

    # 收集 IK 骨骼的子骨骼（尖端骨骼）
    for bone_name in IK_target_bones:
        if bone_name in armature_obj.data.bones:
            bone = armature_obj.data.bones[bone_name]
            for child in bone.children:
                if child.name not in IK_target_tip_bones:
                    IK_target_tip_bones.append(child.name)
                    print(f"【清除 IK】找到 IK 尖端骨骼：{child.name}")

    # 3. 切换到编辑模式，删除 IK 骨骼
    bones_to_delete = set(IK_target_bones + IK_target_tip_bones)
    if bones_to_delete:
        print(f"【清除 IK】待删除骨骼：{bones_to_delete}")
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = armature_obj.data.edit_bones
            for bone_name in bones_to_delete:
                if bone_name in edit_bones:
                    edit_bones.remove(edit_bones[bone_name])
            print("【清除 IK】IK 骨骼删除完成")
        except RuntimeError as e:
            print(f"【清除 IK】删除骨骼失败：{str(e)}")

    # 4. 切换回姿态模式，删除手臂/手部骨骼的约束
    try:
        bpy.ops.object.mode_set(mode='POSE')
        for bone_name in arm_hand_bones:
            if bone_name in armature_obj.pose.bones:
                pose_bone = armature_obj.pose.bones[bone_name]
                # 批量删除所有约束（避免残留 IK）
                while pose_bone.constraints:
                    pose_bone.constraints.remove(pose_bone.constraints[0])
        print("【清除 IK】手臂/手部骨骼约束删除完成")
    except RuntimeError as e:
        print(f"【清除 IK】删除约束失败：{str(e)}")

    # 5. 切换回物体模式
    bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------
# 4. 辅助函数：骨架诊断（检查关键骨骼和现有 IK）
# ------------------------------
def armature_diagnostic(armature_obj):
    """诊断骨架是否满足手臂/手部 IK 添加条件"""
    # 定义需检测的骨骼列表
    print("armature_diagnostic----检测----haohao")
    ENGLISH_ARM_BONES = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    #JAPANESE_ARM_BONES = ["左ひじ", "右ひじ", "左手首", "右手首", "左中指１", "右中指１"]
    JAPANESE_ARM_BONES = ["ひじ.L", "ひじ.R", "手首.L", "手首.R", "中指１.L", "中指１.R"]
    EXISTING_IK_BONES = ["elbow IK_L", "elbow IK_R", "middle1 IK_L", "middle1 IK_R",
                        "elbow_IK_L", "elbow_IK_R", "middle1_IK_L", "middle1_IK_R"]
    bone_keys = armature_obj.data.bones.keys()

    # 检测英文/日文骨骼是否齐全
    english_ok = all(bone in bone_keys for bone in ENGLISH_ARM_BONES)
    japanese_ok = all(bone in bone_keys for bone in JAPANESE_ARM_BONES)
    # 检测是否已存在 IK 骨骼
    has_existing_ik = any(bone in bone_keys for bone in EXISTING_IK_BONES)

    # 打印诊断结果（便于调试）
    print("\n" + "="*50)
    print("【骨架诊断 - 手臂/手部 IK】")
    print(f"\n1. 英文关键骨骼：{ENGLISH_ARM_BONES}")
    print(f"   状态：{'✓ 齐全' if english_ok else '✗ 缺失'}")
    if not english_ok:
        missing = [b for b in ENGLISH_ARM_BONES if b not in bone_keys]
        print(f"   缺失：{missing}")

    print(f"\n2. 日文关键骨骼：{JAPANESE_ARM_BONES}")
    print(f"   状态：{'✓ 齐全' if japanese_ok else '✗ 缺失'}")
    if not japanese_ok:
        missing = [b for b in JAPANESE_ARM_BONES if b not in bone_keys]
        print(f"   缺失：{missing}")

    print(f"\n3. 现有 IK 骨骼：")
    if has_existing_ik:
        found = [b for b in EXISTING_IK_BONES if b in bone_keys]
        print(f"   ✗ 发现 {len(found)} 个：{found}（需先清除）")
    else:
        print(f"   ✓ 无现有 IK 骨骼，可正常添加")
    print("="*50 + "\n")

    # 返回诊断结果（是否满足添加条件）
    return (english_ok or japanese_ok) and not has_existing_ik


# ------------------------------
# 5. 核心函数：创建手臂/手部 IK 骨骼和约束
# ------------------------------
def main(context):
    scene = context.scene
    view_layer = scene.view_layers[0]

    # 1. 找到并激活骨架对象
    active_obj = view_layer.objects.active
    armature_obj = model.findArmature(active_obj)
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        raise Exception("【创建 IK】未找到有效 MMD 骨架对象")
    view_layer.objects.active = armature_obj
    print(f"【创建 IK】当前骨架：{armature_obj.name}")

    # 2. 执行骨架诊断，不满足条件则终止
    diagnostic_ok = armature_diagnostic(armature_obj)
    if not diagnostic_ok:
        raise Exception("【创建 IK】骨架不满足条件（缺失关键骨骼或已存在 IK 骨骼）")

    # 3. 定义手臂/手部关键骨骼的候选名称（支持多语言）
    bone_candidates = {
        "ARM_LEFT": ["左ひじ", "ひじ.L", "elbow_L"],    # 左肘（原代码中变量名对应肘骨骼）
        "ARM_RIGHT": ["右ひじ", "ひじ.R", "elbow_R"],  # 右肘
        "WRIST_LEFT": ["左手首", "手首.L", "wrist_L"], # 左手腕（原代码中变量名误写为 ELBOW_LEFT）
        "WRIST_RIGHT": ["右手首", "手首.R", "wrist_R"],# 右手腕（原代码中变量名误写为 ELBOW_RIGHT）
        "MIDDLE1_LEFT": ["左中指１", "中指１.L", "middle1_L"], # 左中指1节
        "MIDDLE1_RIGHT": ["右中指１", "中指１.R", "middle1_R"]  # 右中指1节
    }

    # 4. 定位关键骨骼（从候选名称中匹配第一个存在的）
    key_bones = {}
    bone_keys = armature_obj.data.bones.keys()
    for bone_type, candidates in bone_candidates.items():
        found = next((b for b in candidates if b in bone_keys), None)
        if not found:
            raise Exception(f"【创建 IK】缺失关键骨骼：{bone_type}（候选：{candidates}）")
        key_bones[bone_type] = found
        print(f"【创建 IK】定位 {bone_type}：{found}")

    # 解包关键骨骼名称（修正原代码变量名与实际骨骼类型的对应关系）
    ARM_LEFT = key_bones["ARM_LEFT"]          # 左肘
    ARM_RIGHT = key_bones["ARM_RIGHT"]        # 右肘
    WRIST_LEFT = key_bones["WRIST_LEFT"]      # 左手腕（原代码误写为 ELBOW_LEFT）
    WRIST_RIGHT = key_bones["WRIST_RIGHT"]    # 右手腕（原代码误写为 ELBOW_RIGHT）
    MIDDLE1_LEFT = key_bones["MIDDLE1_LEFT"]  # 左中指1节
    MIDDLE1_RIGHT = key_bones["MIDDLE1_RIGHT"]# 右中指1节

    # 5. 计算 IK 骨骼长度（基于左手腕骨骼长度）
    wrist_left_bone = armature_obj.data.bones[WRIST_LEFT]
    elbow_length = wrist_left_bone.length  # 以手腕骨骼长度为基准（原代码逻辑）
    DOUBLE_LENGTH_OF_ELBOW_BONE = elbow_length * 2  # IK 主体骨骼长度
    TWENTIETH_LENGTH_OF_ELBOW_BONE = elbow_length * 0.05  # 尖端骨骼长度（极小）
    print(f"【创建 IK】长度计算：基准={elbow_length:.4f} | 主体IK={DOUBLE_LENGTH_OF_ELBOW_BONE:.4f} | 尖端={TWENTIETH_LENGTH_OF_ELBOW_BONE:.4f}")

    # 6. 切换到编辑模式，创建 IK 骨骼
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = armature_obj.data.edit_bones

        # ------------------------------
        # 创建左肘 IK 骨骼（主体 + 尖端）
        # ------------------------------
        # 左肘 IK 主体骨骼（位置：左手腕起点，方向：Z轴负方向）
        bone = edit_bones.new("elbow_IK_L")
        bone.head = edit_bones[WRIST_LEFT].head
        bone.tail = edit_bones[WRIST_LEFT].head.copy()
        bone.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE  # 沿 Z 轴向下延伸
        print(f"【创建 IK】创建左肘 IK 骨骼：elbow_IK_L")

        # 左肘 IK 尖端骨骼（极小，隐藏显示）
        bone_tip = edit_bones.new("elbow_IK_L_t")
        bone_tip.head = bone.head.copy()
        bone_tip.tail = bone.head.copy()
        bone_tip.tail.y += TWENTIETH_LENGTH_OF_ELBOW_BONE  # 沿 Y 轴微调
        bone_tip.parent = bone
        bone_tip.use_connect = False
        print(f"【创建 IK】创建左肘 IK 尖端骨骼：elbow_IK_L_t")

        # ------------------------------
        # 创建右肘 IK 骨骼（主体 + 尖端）
        # ------------------------------
        bone = edit_bones.new("elbow_IK_R")
        bone.head = edit_bones[WRIST_RIGHT].head
        bone.tail = edit_bones[WRIST_RIGHT].head.copy()
        bone.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE
        print(f"【创建 IK】创建右肘 IK 骨骼：elbow_IK_R")

        bone_tip = edit_bones.new("elbow_IK_R_t")
        bone_tip.head = bone.head.copy()
        bone_tip.tail = bone.head.copy()
        bone_tip.tail.y += TWENTIETH_LENGTH_OF_ELBOW_BONE
        bone_tip.parent = bone
        bone_tip.use_connect = False
        print(f"【创建 IK】创建右肘 IK 尖端骨骼：elbow_IK_R_t")

        # ------------------------------
        # 创建左中指 IK 骨骼（主体 + 尖端）
        # ------------------------------
        bone = edit_bones.new("middle1_IK_L")
        bone.head = edit_bones[MIDDLE1_LEFT].head
        bone.tail = edit_bones[MIDDLE1_LEFT].head.copy()
        bone.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE
        bone.parent = edit_bones["elbow_IK_L"]  # 父骨骼设为左肘 IK
        bone.use_connect = False
        print(f"【创建 IK】创建左中指 IK 骨骼：middle1_IK_L（父：elbow_IK_L）")

        bone_tip = edit_bones.new("middle1_IK_L_t")
        bone_tip.head = bone.head.copy()
        bone_tip.tail = bone.head.copy()
        bone_tip.tail.z -= TWENTIETH_LENGTH_OF_ELBOW_BONE
        bone_tip.parent = bone
        bone_tip.use_connect = False
        print(f"【创建 IK】创建左中指 IK 尖端骨骼：middle1_IK_L_t")

        # ------------------------------
        # 创建右中指 IK 骨骼（主体 + 尖端）
        # ------------------------------
        bone = edit_bones.new("middle1_IK_R")
        bone.head = edit_bones[MIDDLE1_RIGHT].head
        bone.tail = edit_bones[MIDDLE1_RIGHT].head.copy()
        bone.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE
        bone.parent = edit_bones["elbow_IK_R"]  # 父骨骼设为右肘 IK
        bone.use_connect = False
        print(f"【创建 IK】创建右中指 IK 骨骼：middle1_IK_R（父：elbow_IK_R）")

        bone_tip = edit_bones.new("middle1_IK_R_t")
        bone_tip.head = bone.head.copy()
        bone_tip.tail = bone.head.copy()
        bone_tip.tail.z -= TWENTIETH_LENGTH_OF_ELBOW_BONE
        bone_tip.parent = bone
        bone_tip.use_connect = False
        print(f"【创建 IK】创建右中指 IK 尖端骨骼：middle1_IK_R_t")

    except RuntimeError as e:
        raise Exception(f"【创建 IK】编辑模式创建骨骼失败：{str(e)}")

    # 7. 切换到姿态模式，隐藏 IK 尖端骨骼（核心修复：使用 hide_bone 函数）
    try:
        bpy.ops.object.mode_set(mode='POSE')
        tip_bones = [
            "elbow_IK_L_t", "elbow_IK_R_t", 
            "middle1_IK_L_t", "middle1_IK_R_t"
        ]
        for tip_name in tip_bones:
            if tip_name in armature_obj.pose.bones:
                pose_bone = armature_obj.pose.bones[tip_name]
                # 使用通用隐藏函数，适配 Blender 3.6
                hide_bone(pose_bone.bone, True)
                # 若为 MMD 骨骼，同步 mmd_bone 属性
                if hasattr(pose_bone, "mmd_bone"):
                    pose_bone.mmd_bone.is_visible = False
                    pose_bone.mmd_bone.is_controllable = False
                    pose_bone.mmd_bone.is_tip = True
        print(f"【创建 IK】隐藏尖端骨骼：{tip_bones}")
    except RuntimeError as e:
        raise Exception(f"【创建 IK】隐藏尖端骨骼失败：{str(e)}")

    # 8. 为手臂/手部骨骼添加 IK 约束
    try:
        # ------------------------------
        # 左肘：添加 IK 约束（控制肘部运动，链长 2）
        # ------------------------------
        ik_const = armature_obj.pose.bones[ARM_LEFT].constraints.new("IK")
        ik_const.name = "MMD_Arm_IK"
        ik_const.target = armature_obj
        ik_const.subtarget = "elbow_IK_L"
        ik_const.chain_count = 2  # 影响肘部 + 上臂
        ik_const.use_tail = True
        ik_const.iterations = 48  # 高迭代次数，确保运动平滑
        print(f"【创建 IK】左肘（{ARM_LEFT}）添加 IK 约束")

        # ------------------------------
        # 右肘：添加 IK 约束（与左肘一致）
        # ------------------------------
        ik_const = armature_obj.pose.bones[ARM_RIGHT].constraints.new("IK")
        ik_const.name = "MMD_Arm_IK"
        ik_const.target = armature_obj
        ik_const.subtarget = "elbow_IK_R"
        ik_const.chain_count = 2
        ik_const.use_tail = True
        ik_const.iterations = 48
        print(f"【创建 IK】右肘（{ARM_RIGHT}）添加 IK 约束")

        # ------------------------------
        # 左手腕：添加 IK 约束（控制手指运动，链长 1）
        # ------------------------------
        ik_const = armature_obj.pose.bones[WRIST_LEFT].constraints.new("IK")
        ik_const.name = "MMD_Hand_IK"
        ik_const.target = armature_obj
        ik_const.subtarget = "middle1_IK_L"
        ik_const.chain_count = 1  # 仅影响手腕
        ik_const.use_tail = True
        ik_const.iterations = 6  # 低迭代次数，快速响应
        print(f"【创建 IK】左手腕（{WRIST_LEFT}）添加 IK 约束")

        # ------------------------------
        # 右手腕：添加 IK 约束（与左手腕一致）
        # ------------------------------
        ik_const = armature_obj.pose.bones[WRIST_RIGHT].constraints.new("IK")
        ik_const.name = "MMD_Hand_IK"
        ik_const.target = armature_obj
        ik_const.subtarget = "middle1_IK_R"
        ik_const.chain_count = 1
        ik_const.use_tail = True
        ik_const.iterations = 6
        print(f"【创建 IK】右手腕（{WRIST_RIGHT}）添加 IK 约束")

    except Exception as e:
        raise Exception(f"【创建 IK】添加约束失败：{str(e)}")

    # 9. 同步 MMD 骨骼属性（若安装 mmd_tools 插件）
    if hasattr(armature_obj.pose.bones[ARM_RIGHT], "mmd_bone"):
        # 肘部 IK 旋转约束（180°）
        armature_obj.pose.bones[ARM_RIGHT].mmd_bone.ik_rotation_constraint = 2
        armature_obj.pose.bones[ARM_LEFT].mmd_bone.ik_rotation_constraint = 2
        # 手腕 IK 旋转约束（360°）
        armature_obj.pose.bones[WRIST_RIGHT].mmd_bone.ik_rotation_constraint = 4
        armature_obj.pose.bones[WRIST_LEFT].mmd_bone.ik_rotation_constraint = 4
        print("【创建 IK】同步 MMD 骨骼 IK 旋转约束属性")

    # 10. 创建 IK 骨骼组，归类管理所有 IK 骨骼
    if "IK" not in armature_obj.pose.bone_groups:
        armature_obj.pose.bone_groups.new(name="IK")
        print("【创建 IK】创建 IK 骨骼组")

    # 将所有 IK 骨骼加入组
    all_ik_bones = [
        "elbow_IK_L", "elbow_IK_R", "middle1_IK_L", "middle1_IK_R",
        "elbow_IK_L_t", "elbow_IK_R_t", "middle1_IK_L_t", "middle1_IK_R_t"
    ]
    for bone_name in all_ik_bones:
        if bone_name in armature_obj.pose.bones:
            armature_obj.pose.bones[bone_name].bone_group = armature_obj.pose.bone_groups["IK"]
    print(f"【创建 IK】所有 IK 骨骼加入 'IK' 组：{all_ik_bones}")

    # 11. 切换回物体模式，完成创建
    bpy.ops.object.mode_set(mode='OBJECT')
    print("【创建 IK】手臂/手部 IK 全部创建完成！")


# ------------------------------
# 6. 操作器类：添加手臂/手部 IK 的按钮逻辑
# ------------------------------
class Add_MMD_Hand_Arm_IK(bpy.types.Operator):
    """为 MMD 模型添加手臂/手部 IK 骨骼和约束"""
    bl_idname = "object.add_hand_arm_ik"  # 操作器唯一ID（与面板关联）
    bl_label = "Add Hand Arm IK to MMD model"
    bl_options = {"REGISTER", "UNDO"}  # 启用撤销功能
    bl_description = "Add arm/hand IK for MMD armature"

    @classmethod
    def poll(cls, context):
        """控制按钮可用性：仅选中对象时可点击"""
        view_layer = context.scene.view_layers[0]
        return bool(view_layer.objects.active)

    def execute(self, context):
        try:
            # 步骤1：先清除现有 IK（避免冲突）
            clear_IK(context)
            # 步骤2：执行 IK 创建逻辑
            main(context)
            # 在 Blender 信息栏显示成功提示
            self.report({"INFO"}, "MMD arm/hand IK added successfully!")
            return {"FINISHED"}
        except Exception as e:
            # 捕获异常，显示错误信息
            self.report({"ERROR"}, str(e))
            print(f"【错误】添加 IK 失败：{str(e)}")
            return {"CANCELLED"}


# ------------------------------
# 7. 插件注册/注销入口
# ------------------------------
def register():
    """注册面板和操作器"""
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK_Panel)
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK)
    print("【MMD Hand/Arm IK】插件注册完成")


def unregister():
    """注销组件（反向顺序，避免依赖错误）"""
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK)
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK_Panel)
    print("【MMD Hand/Arm IK】插件注销完成")


# 直接运行脚本时注册插件（便于测试）
if __name__ == "__main__":
    register()