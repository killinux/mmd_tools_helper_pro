bl_info = {
    "name": "MMD Miscellaneous Tools",
    "author": "Original Author (Adapted for Blender 3.6)",
    "version": (1, 0, 1),
    "blender": (3, 6, 0),  # 明确适配 Blender 3.6
    "location": "View3D > Sidebar > mmd_tools_helper",
    "description": "MMD auxiliary tools: bone merge, vertex group merge, unused asset cleanup",
    "warning": "Requires 'model.py' (from mmd_tools_helper) in the same folder",
    "category": "MMD Tools",
    "support": "COMMUNITY"
}

import bpy

# --------------------------
# 依赖模块容错导入（3.6 适配核心）
# --------------------------
try:
    from . import model  # 骨架/网格查找核心模块
    DEPENDENCIES_LOADED = True
    print("✅ MMD Miscellaneous Tools: 'model.py' loaded successfully")
except ImportError as e:
    DEPENDENCIES_LOADED = False
    MISSING_MODULE = str(e).split("'")[1] if "'" in str(e) else "Unknown"
    print(f"❌ MMD Miscellaneous Tools: Missing module - {MISSING_MODULE}.py")
    print("⚠️  Solution: Place 'model.py' in the same folder as this script")


# --------------------------
# 核心功能函数（3.6 容错增强）
# --------------------------
def all_materials_mmd_ambient_white():
    """将所有非MMD刚体材质的环境色设为白色（需安装 mmd_tools）"""
    # 检查 mmd_tools 材质属性是否存在
    if not hasattr(bpy.types.Material, "mmd_material"):
        raise RuntimeError("mmd_material property not found! Install mmd_tools first.")

    updated_count = 0
    for mat in bpy.data.materials:
        # 排除 MMD 刚体材质
        if "mmd_tools_rigid" not in mat.name.lower():
            # 安全设置环境色（避免属性不存在报错）
            if hasattr(mat, "mmd_material") and hasattr(mat.mmd_material, "ambient_color"):
                mat.mmd_material.ambient_color = (1.0, 1.0, 1.0, 1.0)  # 3.6 支持直接赋值元组
                updated_count += 1

    print(f"\n✅ Set MMD ambient color to white for {updated_count} materials")
    return updated_count


def combine_2_bones_1_bone(parent_bone_name, child_bone_name):
    """合并父子骨骼（父骨骼继承子骨骼尾端位置，删除子骨骼）"""
    active_obj = bpy.context.active_object
    # 前置检查：确保当前对象是骨架
    if not active_obj or active_obj.type != 'ARMATURE':
        raise ValueError("Active object must be an armature")
    if parent_bone_name not in active_obj.data.bones:
        raise KeyError(f"Parent bone '{parent_bone_name}' not found in armature")
    if child_bone_name not in active_obj.data.bones:
        raise KeyError(f"Child bone '{child_bone_name}' not found in armature")

    # 安全切换到编辑模式
    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except Exception as e:
        raise RuntimeError(f"Failed to switch to Edit mode: {str(e)}")

    arm_data = active_obj.data
    # 保存子骨骼尾端位置，赋值给父骨骼
    child_tail = arm_data.edit_bones[child_bone_name].tail.copy()  # 3.6 需用 copy() 避免引用问题
    arm_data.edit_bones[parent_bone_name].tail = child_tail

    # 删除子骨骼
    if child_bone_name in arm_data.edit_bones:
        arm_data.edit_bones.remove(arm_data.edit_bones[child_bone_name])

    # 切回姿态模式
    bpy.ops.object.mode_set(mode='POSE')
    print(f"\n✅ Combined bones: Parent='{parent_bone_name}', Child='{child_bone_name}'")


def combine_2_vg_1_vg(parent_vg_name, child_vg_name):
    """合并父子顶点组（子顶点组权重添加到父顶点组，然后删除子顶点组）"""
    merged_count = 0
    # 遍历场景中所有网格对象
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue  # 仅处理网格对象
        if parent_vg_name not in obj.vertex_groups:
            continue
        if child_vg_name not in obj.vertex_groups:
            continue

        # 获取父/子顶点组
        parent_vg = obj.vertex_groups[parent_vg_name]
        child_vg = obj.vertex_groups[child_vg_name]

        # 遍历所有顶点，合并权重（3.6 顶点索引遍历优化）
        for vert in obj.data.vertices:
            # 检查当前顶点是否在子顶点组中
            try:
                child_weight = child_vg.weight(vert.index)
            except RuntimeError:  # 顶点不在子顶点组中
                continue

            if child_weight > 0:
                # 将子顶点组权重添加到父顶点组
                parent_vg.add([vert.index], child_weight, 'ADD')

        # 删除子顶点组
        obj.vertex_groups.remove(child_vg)
        merged_count += 1
        print(f"✅ Merged vertex groups: Object='{obj.name}', Parent='{parent_vg_name}', Child='{child_vg_name}'")

    if merged_count == 0:
        print(f"\n⚠️ No vertex groups merged (check if '{parent_vg_name}' and '{child_vg_name}' exist)")
    else:
        print(f"\n✅ Total merged vertex groups across {merged_count} objects")


def analyze_selected_parent_child_bone_pair():
    """分析选中的2根骨骼，返回（父骨骼名，子骨骼名），无父子关系则返回None"""
    active_obj = bpy.context.active_object
    if not active_obj or active_obj.type != 'ARMATURE':
        raise ValueError("Active object must be an armature")
    if active_obj.mode != 'POSE':
        raise RuntimeError("Armature must be in Pose mode to select bones")

    # 获取选中的骨骼（仅 Pose 模式有效）
    selected_bones = [b.bone.name for b in active_obj.pose.bones if b.bone.select]

    # 检查选中骨骼数量
    if len(selected_bones) != 2:
        raise ValueError(f"Exactly 2 bones must be selected (current: {len(selected_bones)})")

    bone1, bone2 = selected_bones
    arm_data = active_obj.data

    # 判断父子关系
    if arm_data.bones[bone1].parent == arm_data.bones[bone2]:
        return (bone2, bone1)  # bone2 是父，bone1 是子
    elif arm_data.bones[bone2].parent == arm_data.bones[bone1]:
        return (bone1, bone2)  # bone1 是父，bone2 是子
    else:
        raise ValueError("Selected bones have no parent-child relationship")


def delete_unused_bones():
    """删除名称含 'unused' 的骨骼（不区分大小写）"""
    active_obj = bpy.context.active_object
    if not active_obj or active_obj.type != 'ARMATURE':
        raise ValueError("Active object must be an armature")

    # 切换到编辑模式
    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except Exception as e:
        raise RuntimeError(f"Failed to switch to Edit mode: {str(e)}")

    arm_data = active_obj.data
    deleted_count = 0
    # 遍历编辑模式骨骼（需用 list() 避免遍历中修改集合）
    for bone in list(arm_data.edit_bones):
        if 'unused' in bone.name.lower():
            arm_data.edit_bones.remove(bone)
            deleted_count += 1
            print(f"✅ Deleted unused bone: '{bone.name}'")

    # 切回姿态模式
    bpy.ops.object.mode_set(mode='POSE')

    if deleted_count == 0:
        print("\n⚠️ No unused bones found (look for bones with 'unused' in name)")
    else:
        print(f"\n✅ Total deleted unused bones: {deleted_count}")


def delete_unused_vertex_groups():
    """删除所有网格对象中名称含 'unused' 的顶点组"""
    deleted_count = 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue  # 仅处理网格对象

        # 遍历顶点组（需用 list() 避免遍历中修改）
        for vg in list(obj.vertex_groups):
            if 'unused' in vg.name.lower():
                obj.vertex_groups.remove(vg)
                deleted_count += 1
                print(f"✅ Deleted unused vertex group: Object='{obj.name}', Group='{vg.name}'")

    if deleted_count == 0:
        print("\n⚠️ No unused vertex groups found (look for groups with 'unused' in name)")
    else:
        print(f"\n✅ Total deleted unused vertex groups: {deleted_count}")


def test_is_mmd_english_armature(armature):
    """验证骨架是否为 MMD 英文骨骼（通过关键骨骼名称判断）"""
    if not armature or armature.type != 'ARMATURE':
        return False

    # MMD 英文骨架关键骨骼列表（大小写不敏感）
    mmd_english_key_bones = [
        'upper body', 'neck', 'head', 'shoulder_L', 'arm_L', 'elbow_L',
        'wrist_L', 'leg_L', 'knee_L', 'ankle_L', 'shoulder_R', 'arm_R',
        'elbow_R', 'wrist_R', 'leg_R', 'knee_R', 'ankle_R'
    ]
    arm_bone_names = [b.name.lower() for b in armature.data.bones]
    missing_bones = [b for b in mmd_english_key_bones if b not in arm_bone_names]

    if missing_bones:
        print(f"\n⚠️ MMD English Armature Test Failed: Missing bones - {', '.join(missing_bones)}")
        return False
    print("\n✅ MMD English Armature Test Passed: All key bones exist")
    return True


def correct_root_center():
    """修正 MMD 骨架的 Root 和 Center 骨骼（仅支持 MMD 英文骨骼）"""
    # 1. 找到目标骨架
    armature = model.findArmature(bpy.context.active_object)
    if not armature:
        raise ValueError("No armature found for selected object")
    bpy.context.view_layer.objects.active = armature

    # 2. 验证是否为 MMD 英文骨架
    if not test_is_mmd_english_armature(armature):
        raise RuntimeError("This function only works with MMD English armatures")

    arm_data = armature.data
    updated = False

    # 3. 处理 Root 骨骼（不存在则创建）
    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except Exception as e:
        raise RuntimeError(f"Failed to switch to Edit mode: {str(e)}")

    if "root" not in arm_data.edit_bones:
        # 创建 Root 骨骼
        root_bone = arm_data.edit_bones.new("root")
        root_bone.head = (0.0, 0.0, 0.0)
        root_bone.tail = (0.0, 0.0, 1.0)  # 默认高度 1 单位
        # 将 Center 骨骼设为 Root 子骨骼（若存在）
        if "center" in arm_data.edit_bones:
            arm_data.edit_bones["center"].parent = root_bone
            arm_data.edit_bones["center"].use_connect = False  # 禁用骨骼连接
        print("✅ Created MMD Root bone")
        updated = True

    # 4. 重命名 Center 为 Lower Body 并调整位置
    bpy.ops.object.mode_set(mode='OBJECT')  # 切换到对象模式操作骨骼名称
    if "center" in arm_data.bones:
        # 重命名 Center → Lower Body
        arm_data.bones["center"].name = "lower body"
        print("✅ Renamed 'center' bone to 'lower body'")

        # 调整 Lower Body 骨骼尾端位置（基于左右腿骨骼）
        bpy.ops.object.mode_set(mode='EDIT')
        if all(b in arm_data.edit_bones for b in ["leg_L", "leg_R"]):
            leg_l_head_z = arm_data.edit_bones["leg_L"].head.z
            leg_r_head_z = arm_data.edit_bones["leg_R"].head.z
            arm_data.edit_bones["lower body"].tail.z = 0.5 * (leg_l_head_z + leg_r_head_z)
            print("✅ Adjusted 'lower body' bone tail position")
        updated = True

    # 5. 重建 Center 骨骼（若不存在）
    if "center" not in arm_data.edit_bones:
        center_bone = arm_data.edit_bones.new("center")
        # 基于膝盖和腿骨计算 Center 位置（平均位置）
        if all(b in arm_data.edit_bones for b in ["knee_L", "knee_R", "leg_L", "leg_R"]):
            knee_l = arm_data.edit_bones["knee_L"].head
            knee_r = arm_data.edit_bones["knee_R"].head
            leg_l = arm_data.edit_bones["leg_L"].head
            leg_r = arm_data.edit_bones["leg_R"].head
            # 计算平均位置
            center_head = (knee_l + knee_r + leg_l + leg_r) / 4.0
            center_bone.head = center_head
            center_bone.tail = center_head.copy()
            center_bone.tail.z -= 1.0  # 尾端向下延伸 1 单位
            # 设置父子关系
            if "root" in arm_data.edit_bones:
                center_bone.parent = arm_data.edit_bones["root"]
            if "lower body" in arm_data.edit_bones:
                arm_data.edit_bones["lower body"].parent = center_bone
            if "upper body" in arm_data.edit_bones:
                arm_data.edit_bones["upper body"].parent = center_bone
        print("✅ Created MMD Center bone")
        updated = True

    # 切回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    if not updated:
        print("\n⚠️ No changes made: Root/Center bones are already correct")


# --------------------------
# 主逻辑调度函数
# --------------------------
def main(context):
    """根据用户选择的功能，调度对应核心函数"""
    selected_func = context.scene.selected_miscellaneous_tools
    if selected_func == "none":
        raise ValueError("Please select a function first (in the dropdown menu)")

    # 1. 合并2根骨骼 + 对应的顶点组
    if selected_func == "combine_2_bones":
        armature = model.findArmature(context.active_object)
        if not armature:
            raise ValueError("No armature found for selected object")
        context.view_layer.objects.active = armature
        # 分析选中的父子骨骼
        parent_bone, child_bone = analyze_selected_parent_child_bone_pair()
        # 先合并顶点组，再合并骨骼
        combine_2_vg_1_vg(parent_bone, child_bone)
        combine_2_bones_1_bone(parent_bone, child_bone)

    # 2. 删除无用骨骼和顶点组
    elif selected_func == "delete_unused":
        armature = model.findArmature(context.active_object)
        if not armature:
            raise ValueError("No armature found for selected object")
        context.view_layer.objects.active = armature
        delete_unused_bones()
        delete_unused_vertex_groups()

    # 3. 设置MMD材质环境色为白色
    elif selected_func == "mmd_ambient_white":
        all_materials_mmd_ambient_white()

    # 4. 修正MMD Root/Center骨骼
    elif selected_func == "correct_root_center":
        correct_root_center()


# --------------------------
# UI 面板（3.6 布局优化）
# --------------------------
class MiscellaneousToolsPanel(bpy.types.Panel):
    """杂项工具面板：骨骼合并、顶点组合并、清理等"""
    bl_label = "MMD Miscellaneous Tools"
    bl_idname = "OBJECT_PT_miscellaneous_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 3.6 侧边栏标准区域
    bl_category = "mmd_tools_helper"  # 与其他 MMD 工具统一分类
    bl_order = 13  # 排序：在诊断工具后显示
    bl_options = {'DEFAULT_CLOSED'}  # 默认折叠，减少 UI 占用

    def draw_header(self, context):
        """面板头部：显示图标"""
        self.layout.label(text="", icon='TOOL_SETTINGS')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # 1. 依赖缺失提示（优先显示）
        if not DEPENDENCIES_LOADED:
            col.label(text="❌ Missing Dependencies!", icon='ERROR')
            col.label(text=f"Required: {MISSING_MODULE}.py")
            col.label(text="Place in same folder as main script")
            return

        # 2. 功能选择下拉菜单
        col.label(text="Select Function:", icon='MENU_PANEL')
        col.prop(context.scene, "selected_miscellaneous_tools", text="")
        col.separator()

        # 3. 执行按钮（根据选中功能提示前置条件）
        selected_func = context.scene.selected_miscellaneous_tools
        row = col.row()
        # 按钮可用性控制：依赖加载 + 选中对象 + 选择了功能
        row.enabled = (DEPENDENCIES_LOADED and context.active_object is not None and selected_func != "none")
        
        # 不同功能显示不同提示
        if selected_func == "combine_2_bones":
            row.operator("mmd_tools_helper.miscellaneous_tools", text="Merge Bones + Vertex Groups")
            col.label(text="⚠️  Precondition: 2 parent-child bones selected (Pose mode)", icon='INFO')
        elif selected_func == "delete_unused":
            row.operator("mmd_tools_helper.miscellaneous_tools", text="Delete Unused Assets")
            col.label(text="⚠️  Deletes bones/vertex groups with 'unused' in name", icon='INFO')
        elif selected_func == "mmd_ambient_white":
            row.operator("mmd_tools_helper.miscellaneous_tools", text="Set MMD Ambient to White")
            col.label(text="⚠️  Requires mmd_tools plugin installed", icon='INFO')
        elif selected_func == "correct_root_center":
            row.operator("mmd_tools_helper.miscellaneous_tools", text="Fix MMD Root/Center Bones")
            col.label(text="⚠️  Only works with MMD English armatures", icon='INFO')
        else:
            row.operator("mmd_tools_helper.miscellaneous_tools", text="Execute Selected Function")


# --------------------------
# 操作器（支持 3.6 撤销）
# --------------------------
class MiscellaneousTools(bpy.types.Operator):
    """执行选中的杂项工具功能"""
    bl_idname = "mmd_tools_helper.miscellaneous_tools"
    bl_label = "Execute Miscellaneous Tool"
    bl_description = "Run the selected MMD auxiliary function"
    bl_options = {'REGISTER', 'UNDO'}  # 3.6 必需显式声明 UNDO 支持

    @classmethod
    def poll(cls, context):
        """操作器可用条件：依赖加载 + 有选中对象 + 选择了功能"""
        return (DEPENDENCIES_LOADED 
                and context.active_object is not None 
                and context.scene.selected_miscellaneous_tools != "none")

    def execute(self, context):
        try:
            # 执行主逻辑
            main(context)
            # 状态栏反馈成功
            self.report({'INFO'}, f"Success! Check console for details")
            return {'FINISHED'}

        except Exception as e:
            # 捕获所有异常，状态栏显示精简错误
            error_msg = str(e)[:100]  # 截取前100字符，避免显示过长
            self.report({'ERROR'}, f"Failed: {error_msg}")
            print(f"\n❌ Tool Execution Error: {str(e)}")  # 控制台打印完整错误
            return {'CANCELLED'}


# --------------------------
# 场景属性注册（3.6 规范）
# --------------------------
def register_scene_properties():
    """注册功能选择枚举属性（避免全局污染）"""
    bpy.types.Scene.selected_miscellaneous_tools = bpy.props.EnumProperty(
        items=[
            ('none', 'None (Select a function)', 'No function selected'),
            (
                "combine_2_bones", 
                "Merge 2 Bones + Vertex Groups", 
                "Merge parent-child bones + their vertex groups (select 2 bones in Pose mode)"
            ),
            (
                "delete_unused", 
                "Delete Unused Assets", 
                "Delete bones/vertex groups with 'unused' in name (case-insensitive)"
            ),
            (
                "mmd_ambient_white", 
                "MMD Ambient Color → White", 
                "Set ambient color of all non-rigid MMD materials to white (needs mmd_tools)"
            ),
            (
                "correct_root_center", 
                "Fix MMD Root/Center Bones", 
                "Create/correct MMD Root/Center/Lower Body bones (only MMD English)"
            )
        ],
        name="Select Tool Function",
        default='none',
        description="Choose the MMD auxiliary tool to run"
    )


# --------------------------
# 插件注册/注销（3.6 安全处理）
# --------------------------
def register():
    """注册组件：属性 → 面板 → 操作器"""
    # 1. 注册场景属性
    try:
        register_scene_properties()
        print("✅ MMD Miscellaneous Tools: Scene properties registered")
    except Exception as e:
        print(f"⚠️ MMD Miscellaneous Tools: Failed to register properties - {str(e)}")

    # 2. 注册 UI 面板和操作器
    try:
        bpy.utils.register_class(MiscellaneousToolsPanel)
        bpy.utils.register_class(MiscellaneousTools)
        print("✅ MMD Miscellaneous Tools: UI and operator registered")
    except Exception as e:
        print(f"❌ MMD Miscellaneous Tools: Failed to register classes - {str(e)}")


def unregister():
    """注销组件：避免残留"""
    # 1. 注销操作器和面板
    try:
        bpy.utils.unregister_class(MiscellaneousTools)
        bpy.utils.unregister_class(MiscellaneousToolsPanel)
        print("✅ MMD Miscellaneous Tools: UI and operator unregistered")
    except Exception as e:
        print(f"⚠️ MMD Miscellaneous Tools: Failed to unregister classes - {str(e)}")

    # 2. 安全删除场景属性
    try:
        if hasattr(bpy.types.Scene, "selected_miscellaneous_tools"):
            del bpy.types.Scene.selected_miscellaneous_tools
            print("✅ MMD Miscellaneous Tools: Scene properties deleted")
    except Exception as e:
        print(f"⚠️ MMD Miscellaneous Tools: Failed to delete properties - {str(e)}")


# 直接运行时注册（测试用）
if __name__ == "__main__":
    register()