bl_info = {
    "name": "MMD Armature Diagnostic",
    "author": "Original Author (Adapted for Blender 3.6)",
    "version": (1, 0, 1),
    "blender": (3, 6, 0),  # 明确适配 Blender 3.6
    "location": "View3D > Sidebar > mmd_tools_helper",
    "description": "Diagnoses MMD armatures: checks missing bones and lists all bones",
    "warning": "Requires 'import_csv.py' and 'model.py' (from mmd_tools_helper)",
    "category": "MMD Tools",
    "support": "COMMUNITY"
}

import bpy

# --------------------------
# 依赖模块容错导入（Blender 3.6 适配）
# --------------------------
try:
    from . import import_csv
    from . import model
    DEPENDENCIES_LOADED = True
    print("✅ Armature Diagnostic: Dependencies (import_csv.py/model.py) loaded")
except ImportError as e:
    DEPENDENCIES_LOADED = False
    MISSING_MODULE = str(e).split("'")[1] if "'" in str(e) else "Unknown"
    print(f"❌ Armature Diagnostic: Missing module - {MISSING_MODULE}.py")
    print("⚠️  Solution: Place 'import_csv.py' and 'model.py' in the same folder as this script")


# --------------------------
# UI 面板（3.6 布局优化）
# --------------------------
class ArmatureDiagnosticPanel(bpy.types.Panel):
    """骨架诊断面板：检查缺失骨骼并打印骨骼列表"""
    bl_label = "MMD Armature Diagnostic"
    bl_idname = "OBJECT_PT_armature_diagnostic"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 3.6 侧边栏标准区域（替代旧版 TOOLS）
    bl_category = "mmd_tools_helper"  # 侧边栏标签页（与其他 MMD 工具统一）
    bl_order = 12  # 排序：在 MMD 工具面板后显示
    bl_options = {'DEFAULT_CLOSED'}  # 默认折叠，减少 UI 占用

    def draw_header(self, context):
        """面板头部：显示图标"""
        self.layout.label(text="", icon="DIAGNOSTIC")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # 1. 依赖缺失提示（优先显示）
        if not DEPENDENCIES_LOADED:
            col.label(text="❌ Missing Dependencies!", icon='ERROR')
            col.label(text=f"Required: {MISSING_MODULE}.py")
            col.label(text="Place in same folder as main script")
            return

        # 2. 骨架类型选择（下拉菜单）
        col.label(text="Target Bone Type:", icon='ARMATURE_DATA')
        col.prop(context.scene, "selected_armature_to_diagnose", text="")
        col.separator()

        # 3. 诊断按钮（仅选中对象时可用）
        row = col.row()
        row.enabled = (context.active_object is not None)  # 按钮可用性控制
        row.operator(
            "mmd_tools_helper.armature_diagnostic",
            text="Run Armature Diagnostic",
            icon='PLAY'
        )

        # 4. 操作提示
        col.label(text="ℹ️  Check Console for Results", icon='INFO')


# --------------------------
# 核心诊断逻辑（3.6 容错增强）
# --------------------------
def diagnose_missing_bones(context, armature, target_bone_type):
    """
    检测骨架中缺失的骨骼
    :param context: Blender 上下文
    :param armature: 目标骨架对象
    :param target_bone_type: 待诊断的骨骼类型（如 mmd_english）
    :return: 缺失的骨骼列表
    """
    missing_bones = []

    # 1. 加载骨骼字典（容错处理）
    try:
        main_bone_dict = import_csv.use_csv_bones_dictionary()  # 主体骨骼字典
        finger_bone_dict = import_csv.use_csv_bones_fingers_dictionary()  # 手指骨骼字典
    except Exception as e:
        raise RuntimeError(f"Failed to load bone dictionaries: {str(e)}")

    # 2. 检查字典有效性
    if not (main_bone_dict and finger_bone_dict and len(main_bone_dict) > 0 and len(finger_bone_dict) > 0):
        raise ValueError("Bone dictionaries are empty or invalid (check CSV files)")

    # 3. 确认目标骨骼类型在字典中
    if target_bone_type not in main_bone_dict[0] or target_bone_type not in finger_bone_dict[0]:
        raise ValueError(f"Target bone type '{target_bone_type}' not found in dictionaries")

    # 4. 获取目标骨骼类型的索引
    main_idx = main_bone_dict[0].index(target_bone_type)
    finger_idx = finger_bone_dict[0].index(target_bone_type)

    # 5. 获取骨架中已存在的骨骼
    existing_bones = set(armature.data.bones.keys())  # 用集合提升查询效率

    # 6. 检查主体骨骼缺失
    for bone_entry in main_bone_dict[1:]:  # 跳过表头行
        bone_name = bone_entry[main_idx]
        # 过滤无效骨骼名称（空值、特殊非必需骨骼）
        if (bone_name 
            and bone_name.strip() 
            and bone_name not in ["upper body 2", "上半身2"]):
            if bone_name not in existing_bones:
                missing_bones.append(bone_name)

    # 7. 检查手指骨骼缺失
    for bone_entry in finger_bone_dict[1:]:  # 跳过表头行
        bone_name = bone_entry[finger_idx]
        # 过滤无效骨骼名称
        if (bone_name 
            and bone_name.strip() 
            and bone_name not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]):
            if bone_name not in existing_bones:
                missing_bones.append(bone_name)

    return sorted(missing_bones)  # 排序后返回，便于阅读


def print_all_bones(armature):
    """打印骨架中所有非辅助骨骼（排除 dummy/shadow 等）"""
    # 过滤规则：排除名称含 "dummy" 或 "shadow" 的骨骼（不区分大小写）
    valid_bones = [
        bone.name for bone in armature.data.bones 
        if not ("dummy" in bone.name.lower() or "shadow" in bone.name.lower())
    ]

    # 控制台打印格式化结果
    print("\n" + "="*60)
    print(f"📊 All Valid Bones in Armature: {armature.name}")
    print(f"Total Bones: {len(valid_bones)}")
    print("-"*60)
    for i, bone in enumerate(valid_bones, 1):
        print(f"{i:3d}. {bone}")  # 带序号，便于计数
    print("="*60 + "\n")


# --------------------------
# 诊断操作器（支持 Blender 3.6 撤销）
# --------------------------
class ArmatureDiagnostic(bpy.types.Operator):
    """执行骨架诊断：打印骨骼列表 + 检测缺失骨骼"""
    bl_idname = "mmd_tools_helper.armature_diagnostic"
    bl_label = "Run Armature Diagnostic"
    bl_description = "Lists all bones and checks missing bones for selected type"
    bl_options = {'REGISTER', 'UNDO'}  # 3.6 必需显式声明 UNDO 支持

    @classmethod
    def poll(cls, context):
        """操作器可用条件：依赖加载完成 + 有选中对象"""
        return DEPENDENCIES_LOADED and context.active_object is not None

    def execute(self, context):
        try:
            # 1. 找到目标骨架（支持选中网格/骨架对象）
            armature = model.findArmature(context.active_object)
            if not armature or armature.type != 'ARMATURE':
                self.report({'ERROR'}, "No valid armature found for selected object")
                return {'CANCELLED'}

            # 2. 打印所有骨骼列表
            print_all_bones(armature)

            # 3. 获取用户选择的诊断骨骼类型
            target_bone_type = context.scene.selected_armature_to_diagnose

            # 4. 检测缺失骨骼
            missing_bones = diagnose_missing_bones(context, armature, target_bone_type)

            # 5. 打印缺失骨骼报告
            print("\n" + "="*60)
            print(f"🔍 Missing Bones Report (Target Type: {target_bone_type})")
            print(f"Armature: {armature.name}")
            print(f"Missing Bones Count: {len(missing_bones)}")
            print("-"*60)
            if missing_bones:
                for i, bone in enumerate(missing_bones, 1):
                    print(f"{i:3d}. {bone}")
                # MMD 英文骨骼特殊提示
                if target_bone_type == 'mmd_english':
                    print("\n⚠️ Note: 'upper body 2', 'thumb0_L', 'thumb0_R' are non-essential MMD bones")
            else:
                print("✅ No missing bones! All required bones exist.")
            print("="*60 + "\n")

            # 6. 状态栏反馈成功信息
            self.report({'INFO'}, f"Diagnostic done! Check console (Missing: {len(missing_bones)})")
            return {'FINISHED'}

        except Exception as e:
            # 错误捕获与反馈
            error_msg = str(e)[:100]  # 截取前100字符，避免状态栏显示过长
            self.report({'ERROR'}, f"Diagnostic failed: {error_msg}")
            print(f"❌ Diagnostic Error: {str(e)}")
            return {'CANCELLED'}


# --------------------------
# 场景属性注册（3.6 规范）
# --------------------------
def register_scene_properties():
    """注册骨骼类型选择枚举属性（移至 register 内，避免全局污染）"""
    bone_type_items = [
        ('mmd_english', 'MMD English', 'MMD 英文骨骼（Hips/Spine）'),
        ('mmd_japanese', 'MMD Japanese', 'MMD 日文骨骼（骨盤/背骨）'),
        ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MMD 日文骨骼（带 .L/.R 后缀）'),
        ('xna_lara', 'XNALara', 'XNALara 骨骼命名'),
        ('daz_poser', 'DAZ/Poser', 'DAZ/Poser/Second Life 骨骼'),
        ('blender_rigify', 'Blender Rigify', 'Blender Rigify 预绑定骨骼'),
        ('sims_2', 'Sims 2', '模拟人生 2 骨骼'),
        ('motion_builder', 'Motion Builder', 'Motion Builder 骨骼'),
        ('3ds_max', '3ds Max', '3ds Max 标准骨骼'),
        ('bepu', 'Bepu IK', 'Bepu 全身 IK 骨骼'),
        ('project_mirai', 'Project Mirai', '初音未来：未来计划 骨骼'),
        ('manuel_bastioni_lab', 'Manuel Bastioni', 'Manuel Bastioni Lab 骨骼'),
        ('makehuman_mhx', 'MakeHuman MHX', 'MakeHuman MHX 导出骨骼'),
        ('sims_3', 'Sims 3', '模拟人生 3 骨骼'),
        ('doa5lr', 'DOA5LR', '死或生 5 骨骼'),
        ('Bip_001', 'Bip001', '标准 Bip001 骨骼（UE/Unity）'),
        ('biped_3ds_max', '3DS Max Biped', '3ds Max Biped 骨骼'),
        ('biped_sfm', 'SFM Biped', 'Source Film Maker Biped 骨骼'),
        ('valvebiped', 'ValveBiped', 'Valve 骨骼（TF2/CS:GO）'),
        ('iClone7', 'iClone7', 'iClone7 角色骨骼')
    ]

    # 注册骨骼类型选择属性
    bpy.types.Scene.selected_armature_to_diagnose = bpy.props.EnumProperty(
        items=bone_type_items,
        name="Target Bone Type",
        default='mmd_english',  # 默认诊断 MMD 英文骨骼
        description="Select the bone type to check for missing bones"
    )


# --------------------------
# 插件注册/注销（3.6 安全处理）
# --------------------------
def register():
    """注册插件组件：属性 → 面板 → 操作器"""
    # 1. 注册场景属性
    try:
        register_scene_properties()
        print("✅ Armature Diagnostic: Scene properties registered")
    except Exception as e:
        print(f"⚠️ Armature Diagnostic: Failed to register properties - {str(e)}")

    # 2. 注册 UI 面板和操作器
    try:
        bpy.utils.register_class(ArmatureDiagnosticPanel)
        bpy.utils.register_class(ArmatureDiagnostic)
        print("✅ Armature Diagnostic: UI and operator registered")
    except Exception as e:
        print(f"❌ Armature Diagnostic: Failed to register classes - {str(e)}")


def unregister():
    """注销插件组件：避免残留"""
    # 1. 注销操作器和面板
    try:
        bpy.utils.unregister_class(ArmatureDiagnostic)
        bpy.utils.unregister_class(ArmatureDiagnosticPanel)
        print("✅ Armature Diagnostic: UI and operator unregistered")
    except Exception as e:
        print(f"⚠️ Armature Diagnostic: Failed to unregister classes - {str(e)}")

    # 2. 安全删除场景属性（避免 AttributeError）
    try:
        if hasattr(bpy.types.Scene, "selected_armature_to_diagnose"):
            del bpy.types.Scene.selected_armature_to_diagnose
            print("✅ Armature Diagnostic: Scene properties deleted")
    except Exception as e:
        print(f"⚠️ Armature Diagnostic: Failed to delete properties - {str(e)}")


# 直接运行时注册（测试用）
if __name__ == "__main__":
    register()