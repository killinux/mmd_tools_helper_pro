import bpy
from . import import_csv  # 需确保同目录下有 import_csv.py 模块
from . import model       # 需确保同目录下有 model.py 模块（含 findArmature 函数）


# ------------------------------
# 1. 面板类（适配 Blender 2.8+ UI 结构）
# ------------------------------
class ArmatureDiagnosticPanel(bpy.types.Panel):
    """骨架诊断面板（显示在 3D 视图侧边栏）"""
    bl_label = "Armature Diagnostic Panel"  # 面板显示名称
    bl_idname = "OBJECT_PT_armature_diagnostic"  # 唯一ID（不可重复）
    bl_space_type = "VIEW_3D"  # 所在空间：3D 视图
    bl_region_type = "UI"      # 所在区域：侧边栏（Blender 2.8+ 废弃 TOOLS 区域）
    bl_category = "mmd_tools_helper"  # 侧边栏标签（无则手动在 Blender 中创建）
    bl_context = "objectmode"  # 仅在物体模式下显示（避免编辑模式报错）

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view_layer = scene.view_layers[0]  # 从视图层获取活跃对象（关键修复）

        # 1. 选择要诊断的骨架类型（枚举属性）
        layout.prop(scene, "selected_armature_to_diagnose", text="Armature Type")
        
        # 2. 标题与分隔符（优化布局美观度）
        layout.separator()
        row = layout.row()
        row.label(text="Armature Diagnostic", icon="ARMATURE_DATA")  # 带骨架图标

        # 3. 诊断按钮（仅当选中有效对象时可点击）
        layout.separator()
        row = layout.row()
        row.operator("mmd_tools_helper.armature_diagnostic", text="Diagnose Armature")
        # 按钮可用性控制：仅选中对象时启用（避免空对象报错）
        row.enabled = bool(view_layer.objects.active)


# ------------------------------
# 2. 核心诊断逻辑（修复活跃对象获取路径）
# ------------------------------
def main(context):
    missing_bone_names = []
    scene = context.scene
    view_layer = scene.view_layers[0]  # 关键：从视图层获取活跃对象（Blender 2.8+ 必需）

    # 1. 读取 CSV 骨骼字典（容错处理：避免模块缺失或读取失败导致崩溃）
    try:
        BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        print(f"【错误】读取骨骼字典失败：{str(e)}")
        return

    # 2. 验证字典格式（首行需为骨骼类型列表）
    if not (isinstance(BONE_NAMES_DICTIONARY, list) and len(BONE_NAMES_DICTIONARY) > 0):
        print("【错误】普通骨骼字典格式无效（需为非空列表）")
        return
    if not (isinstance(FINGER_BONE_NAMES_DICTIONARY, list) and len(FINGER_BONE_NAMES_DICTIONARY) > 0):
        print("【错误】手指骨骼字典格式无效（需为非空列表）")
        return

    # 3. 获取选中的骨骼类型及索引（容错：避免类型不存在导致崩溃）
    SelectedBoneMap = scene.selected_armature_to_diagnose
    try:
        BoneMapIndex = BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
        FingerBoneMapIndex = FINGER_BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
    except ValueError:
        print(f"【错误】选中的骨骼类型「{SelectedBoneMap}」不在字典中")
        return

    # 4. 找到并激活骨架对象（依赖 model.findArmature 函数）
    active_obj = view_layer.objects.active  # 从视图层拿活跃对象（而非 scene）
    armature_obj = model.findArmature(active_obj)
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("【错误】未找到有效骨架对象（选中对象或其关联对象需为骨架）")
        return
    view_layer.objects.active = armature_obj  # 在视图层中激活骨架（关键修复）

    # 5. 检测普通骨骼是否缺失
    for bone_entry in BONE_NAMES_DICTIONARY[1:]:  # 跳过首行（骨骼类型列表）
        # 避免索引越界（容错：处理字典行长度不一致的情况）
        if len(bone_entry) <= BoneMapIndex:
            continue
        target_bone = bone_entry[BoneMapIndex]
        # 跳过空名称和排除列表（原逻辑保留）
        if (target_bone != "" 
            and target_bone not in ["upper body 2", "上半身2"]
            and target_bone not in armature_obj.data.bones):
            missing_bone_names.append(target_bone)

    # 6. 检测手指骨骼是否缺失
    for finger_entry in FINGER_BONE_NAMES_DICTIONARY[1:]:  # 跳过首行
        if len(finger_entry) <= FingerBoneMapIndex:
            continue
        target_finger_bone = finger_entry[FingerBoneMapIndex]
        if (target_finger_bone != ""
            and target_finger_bone not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]
            and target_finger_bone not in armature_obj.data.bones):
            missing_bone_names.append(target_finger_bone)

    # 7. 打印诊断结果（优化格式，便于阅读）
    print("\n" + "="*50)
    print(f"【骨架诊断结果】选中的骨骼类型：{SelectedBoneMap}")
    print(f"【缺失骨骼列表】共 {len(missing_bone_names)} 个缺失骨骼：")
    if missing_bone_names:
        for idx, bone in enumerate(missing_bone_names, 1):
            print(f"  {idx}. {bone}")
    else:
        print("  无缺失骨骼（骨架完整性良好）")
    
    # 8. MMD 英文骨骼特殊提示（原逻辑保留）
    if SelectedBoneMap == "mmd_english":
        print("\n【提示】以下 3 个骨骼为 MMD 半标准骨骼，非必需：")
        print("  - upper body 2（上半身2）")
        print("  - thumb0_L（左手拇指0）")
        print("  - thumb0_R（右手拇指0）")
    print("="*50 + "\n")


# ------------------------------
# 3. 操作器类（诊断按钮逻辑）
# ------------------------------
class ArmatureDiagnostic(bpy.types.Operator):
    """骨架诊断操作器（点击按钮时执行）"""
    bl_idname = "mmd_tools_helper.armature_diagnostic"  # 操作器唯一ID（与面板按钮关联）
    bl_label = "Armature Diagnostic"                    # 操作器显示名称
    bl_options = {"REGISTER", "UNDO"}                   # 启用注册和撤销功能（提升用户体验）

    # 控制操作器可用性：仅当选中对象时可点击（避免空对象报错）
    @classmethod
    def poll(cls, context):
        view_layer = context.scene.view_layers[0]
        return bool(view_layer.objects.active)  # 仅选中对象时启用按钮

    def execute(self, context):
        scene = context.scene
        view_layer = scene.view_layers[0]

        # 1. 找到并激活骨架对象
        active_obj = view_layer.objects.active
        armature_obj = model.findArmature(active_obj)
        if not (armature_obj and armature_obj.type == "ARMATURE"):
            self.report({"ERROR"}, "未找到有效骨架对象！")  # 在 Blender 信息栏提示错误
            return {"CANCELLED"}  # 终止操作

        # 2. 打印当前骨架的所有骨骼名称（排除含 "dummy" 和 "shadow" 的骨骼）
        valid_bones = [
            b.name for b in armature_obj.data.bones 
            if "dummy" not in b.name.lower() and "shadow" not in b.name.lower()
        ]
        print("\n" + "="*50)
        print(f"【当前骨架信息】名称：{armature_obj.name}")
        print(f"【有效骨骼列表】共 {len(valid_bones)} 个骨骼：")
        for idx, bone in enumerate(sorted(valid_bones), 1):  # 排序后打印，便于查找
            print(f"  {idx}. {bone}")
        print("="*50 + "\n")

        # 3. 执行核心诊断逻辑
        main(context)

        # 4. 在 Blender 信息栏显示成功提示
        self.report({"INFO"}, "骨架诊断完成！详见系统控制台输出")
        return {"FINISHED"}  # 标记操作成功


# ------------------------------
# 4. 注册场景属性（骨骼类型枚举）
# ------------------------------
def register_scene_properties():
    """注册场景级枚举属性（供面板选择骨骼类型）"""
    # 骨骼类型选项列表（优化原代码拼写错误：MikuMikuDamce → MikuMikuDance）
    bone_type_items = [
        ('mmd_english', 'MMD English', 'MikuMikuDance English bone names'),
        ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bone names'),
        ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MikuMikuDance Japanese bones with .L.R suffixes'),
        ('xna_lara', 'XNALara', 'XNALara bone names'),
        ('daz_poser', 'DAZ/Poser', 'DAZ/Poser bone names'),
        ('blender_rigify', 'Blender Rigify', 'Blender Rigify bone names (pre-rig)'),
        ('sims_2', 'Sims 2', 'Sims 2 bone names'),
        ('motion_builder', 'Motion Builder', 'Motion Builder bone names'),
        ('3ds_max', '3ds Max', '3ds Max bone names'),
        ('bepu', 'Bepu Full-Body IK', 'Bepu full body IK bone names'),
        ('project_mirai', 'Project Mirai', 'Project Mirai bone names'),
        ('manuel_bastioni_lab', 'Manuel Bastioni Lab', 'Manuel Bastioni Lab bone names'),
        ('makehuman_mhx', 'MakeHuman MHX', 'MakeHuman MHX bone names'),
        ('sims_3', 'Sims 3', 'Sims 3 bone names'),
        ('doa5lr', 'DOA5LR', 'Dead or Alive 5 Last Round bone names'),
        ('Bip_001', 'Bip001', 'Bip001 bone names'),
        ('biped_3ds_max', 'Biped (3ds Max)', 'Biped 3DS Max bone names'),
        ('biped_sfm', 'Biped (SFM)', 'Biped Source Film Maker bone names'),
        ('valvebiped', 'ValveBiped', 'ValveBiped bone names'),
        ('iClone7', 'iClone 7', 'iClone7 bone names')
    ]

    # 注册场景属性（供面板和逻辑调用）
    bpy.types.Scene.selected_armature_to_diagnose = bpy.props.EnumProperty(
        items=bone_type_items,
        name="Armature Type",
        description="Select the bone type to diagnose against",
        default='mmd_english'  # 默认选中 MMD 英文骨骼
    )


def unregister_scene_properties():
    """注销场景属性（避免 Blender 内存泄漏）"""
    if hasattr(bpy.types.Scene, "selected_armature_to_diagnose"):
        del bpy.types.Scene.selected_armature_to_diagnose


# ------------------------------
# 5. 插件注册/注销入口（规范 Blender 插件生命周期）
# ------------------------------
def register():
    """注册插件所有组件（面板、操作器、属性）"""
    register_scene_properties()
    bpy.utils.register_class(ArmatureDiagnosticPanel)
    bpy.utils.register_class(ArmatureDiagnostic)
    print("【Armature Diagnostic】插件注册完成！")


def unregister():
    """注销插件所有组件（反向顺序，避免依赖错误）"""
    bpy.utils.unregister_class(ArmatureDiagnostic)
    bpy.utils.unregister_class(ArmatureDiagnosticPanel)
    unregister_scene_properties()
    print("【Armature Diagnostic】插件注销完成！")


# 直接运行脚本时注册插件（便于测试）
if __name__ == "__main__":
    register()