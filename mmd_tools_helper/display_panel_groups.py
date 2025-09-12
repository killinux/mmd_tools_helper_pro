import bpy
from . import model
from . import import_csv

# ------------------------------
# 辅助函数：兼容MMD Tools不同版本的Display Item Frame结构
# ------------------------------
def __items(display_item_frame):
    """获取显示面板组的子项列表（处理mmd_tools版本差异）"""
    return getattr(display_item_frame, 'data', display_item_frame.items)

# ------------------------------
# 1. 场景属性注册（符合Blender 3.x规范，避免残留）
# ------------------------------
def register_scene_properties():
    # 显示面板组生成选项（枚举属性）
    bpy.types.Scene.display_panel_options = bpy.props.EnumProperty(
        items=[
            ('no_change', 'No Change', '不修改现有显示面板组'),
            ('display_panel_groups_from_bone_groups', 'From Bone Groups', '从骨骼组生成显示面板组'),
            ('add_display_panel_groups', 'Custom Groups', '按自定义规则生成显示面板组')
        ],
        name="MMD Display Panel Groups",
        default='no_change',
        description="选择MMD显示面板组的生成方式"
    )

def unregister_scene_properties():
    # 注销时清理场景属性，防止内存残留
    if hasattr(bpy.types.Scene, "display_panel_options"):
        del bpy.types.Scene.display_panel_options

# ------------------------------
# 2. 面板类（适配Blender 3.6侧边栏UI）
# ------------------------------
class MmdToolsDisplayPanelGroupsPanel(bpy.types.Panel):
    """批量添加骨骼名/形状键名到MMD显示面板组"""
    bl_idname = "OBJECT_PT_mmd_add_display_panel_groups"
    bl_label = "MMD Display Panel Groups"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 关键：Blender 2.8+ 用UI替代废弃的TOOLS（侧边栏，按N键显示）
    bl_category = "mmd_tools_helper"  # 面板归类到MMD工具助手
    bl_order = 6  # 侧边栏中的显示顺序（可选）

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 标题与说明
        row = layout.row()
        row.label(text="生成MMD显示面板组", icon="ARMATURE_DATA")
        
        # 生成方式选择（枚举属性）
        row = layout.row()
        layout.prop(scene, "display_panel_options", expand=False)
        
        # 执行按钮（放大尺寸，提升点击体验）
        row = layout.row()
        row.scale_y = 1.2
        row.operator(
            "object.add_display_panel_groups",
            text="生成显示面板项",
            icon="GROUP"
        )

# ------------------------------
# 3. 核心功能函数（修复API兼容与逻辑bug）
# ------------------------------
def delete_empty_display_panel_groups(root):
    """删除空的显示面板组（避免冗余）"""
    bpy.context.view_layer.objects.active = root
    # 倒序遍历：防止删除后索引错乱
    for d_idx in range(len(root.mmd_root.display_item_frames)-1, 1, -1):
        frame = root.mmd_root.display_item_frames[d_idx]
        if len(__items(frame)) == 0:
            root.mmd_root.display_item_frames.remove(d_idx)

def clear_display_panel_groups(root):
    """清空所有显示面板组（重新生成前调用）"""
    bpy.context.view_layer.objects.active = root
    root.mmd_root.display_item_frames.clear()

def display_panel_groups_from_bone_groups(root, armature_object):
    """从骨骼组生成显示面板组"""
    # 切换到POSE模式，获取骨骼组信息
    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='POSE')
    
    # 收集所有骨骼组名称 + "Other"（无骨骼组的骨骼归为此类）
    bone_groups = list(armature_object.pose.bone_groups.keys()) + ["Other"]
    bone_groups_of_bones = []  # 存储 (骨骼名, 所属组名)

    # 遍历骨骼，分配到对应分组
    for pose_bone in armature_object.pose.bones:
        bone_name = pose_bone.name
        # 过滤：排除dummy/shadow骨骼
        if "dummy" in bone_name.lower() or "shadow" in bone_name.lower():
            continue
        
        # 特殊处理：根骨骼（root/center/全ての親/センター）
        if bone_name in ["root", "全ての親", "center", "センター"]:
            bone_groups_of_bones.append((bone_name, "Root"))
            continue
        
        # 按骨骼组分配，无组则归为"Other"
        if pose_bone.bone_group is not None:
            bone_groups_of_bones.append((bone_name, pose_bone.bone_group.name))
        else:
            bone_groups_of_bones.append((bone_name, "Other"))
    
    # 切换到MMD根对象，创建显示面板组
    bpy.context.view_layer.objects.active = root
    # 1. 创建特殊面板组：Root（根骨骼）、表情（Morph专用）
    root_frame = root.mmd_root.display_item_frames.add()
    root_frame.name = "Root"
    root_frame.name_e = "Root"
    root_frame.is_special = True
    
    exp_frame = root.mmd_root.display_item_frames.add()
    exp_frame.name = "表情"
    exp_frame.name_e = "Expressions"
    exp_frame.is_special = True
    
    # 2. 创建骨骼组对应的面板组
    for bg_name in bone_groups:
        if bg_name not in ["Root", "表情"]:
            frame = root.mmd_root.display_item_frames.add()
            frame.name = bg_name
            frame.name_e = bg_name
    
    # 3. 将骨骼添加到对应面板组
    for bone_name, group_name in bone_groups_of_bones:
        # 找到目标面板组
        target_frame = next((f for f in root.mmd_root.display_item_frames if f.name == group_name), None)
        if target_frame:
            item = __items(target_frame).add()
            item.name = bone_name
            item.name_e = bone_name

def display_panel_groups_from_shape_keys(mesh_objects_list):
    """从形状键生成「表情」面板组项（排除SDEF和Basis）"""
    shape_key_names = set()  # 用set自动去重

    # 收集所有有效形状键
    for mesh_obj in mesh_objects_list:
        if not mesh_obj.data.shape_keys:
            continue
        for sk in mesh_obj.data.shape_keys.key_blocks:
            if "sdef" not in sk.name.lower() and sk.name != "Basis":
                shape_key_names.add(sk.name)
    
    # 将形状键添加到「表情」面板组
    for mesh_obj in mesh_objects_list:
        root = model.findRoot(mesh_obj)
        if not root:
            continue
        # 找到「表情」面板组
        exp_frame = next((f for f in root.mmd_root.display_item_frames if f.name == "表情"), None)
        if not exp_frame:
            continue
        # 避免重复添加
        existing_names = [item.name for item in __items(exp_frame)]
        for sk_name in shape_key_names:
            if sk_name not in existing_names:
                item = __items(exp_frame).add()
                item.type = 'MORPH'
                item.morph_type = 'vertex_morphs'
                item.name = sk_name

def display_panel_groups_non_vertex_morphs(root):
    """添加非顶点Morph（骨骼/材质/UV/组）到「表情」面板组"""
    bpy.context.view_layer.objects.active = root
    # 找到「表情」面板组
    exp_frame = next((f for f in root.mmd_root.display_item_frames if f.name == "表情"), None)
    if not exp_frame:
        return
    
    existing_names = [item.name for item in __items(exp_frame)]

    # 1. 骨骼Morph
    for morph in root.mmd_root.bone_morphs:
        if morph.name not in existing_names:
            item = __items(exp_frame).add()
            item.type = 'MORPH'
            item.morph_type = "bone_morphs"
            item.name = morph.name
    
    # 2. 材质Morph
    for morph in root.mmd_root.material_morphs:
        if morph.name not in existing_names:
            item = __items(exp_frame).add()
            item.type = 'MORPH'
            item.morph_type = "material_morphs"
            item.name = morph.name
    
    # 3. UV Morph
    for morph in root.mmd_root.uv_morphs:
        if morph.name not in existing_names:
            item = __items(exp_frame).add()
            item.type = 'MORPH'
            item.morph_type = "uv_morphs"
            item.name = morph.name
    
    # 4. 组Morph
    for morph in root.mmd_root.group_morphs:
        if morph.name not in existing_names:
            item = __items(exp_frame).add()
            item.type = 'MORPH'
            item.morph_type = "group_morphs"
            item.name = morph.name

# ------------------------------
# 自定义显示面板组规则（基于骨骼名称+IK约束）
# ------------------------------
# 预定义面板组（英文/日文）
My_Display_Panel_Groups = [
    ("Root", "Root"),
    ("Expressions", "表情"),
    ("IK", "ＩＫ"),
    ("Head", "頭"),
    ("Fingers", "指"),
    ("Hair", "髪"),
    ("Skirt", "スカト"),
    ("Body", "体"),
    ("Other", "Other"),
]

def display_panel_groups_create(root, armature_object):
    """按自定义规则生成显示面板组（骨骼名称匹配+IK约束）"""
    # 加载CSV骨骼字典（依赖import_csv模块）
    try:
        BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        raise Exception(f"加载骨骼字典失败：{str(e)}")
    
    bpy.context.view_layer.objects.active = armature_object
    items_added = []  # 记录已添加骨骼，避免重复

    # 1. 定义骨骼匹配关键词
    head_keywords = ["Head", "head", "頭", "eye", "nose", "tongue", "lip", "jaw", "brow", "cheek", "mouth", "nostril"]
    hair_keywords = ["Hair", "hair", "髪"]
    skirt_keywords = ["Skirt", "skirt", "スカト", "スカート"]
    
    # 根骨骼名称（从CSV字典+补充）
    root_names = BONE_NAMES_DICTIONARY[1] if len(BONE_NAMES_DICTIONARY) > 1 else []
    root_names += ["center", "Center", "センター"]
    
    # 身体骨骼名称（从CSV字典筛选）
    body_names = []
    for idx, bone_group in enumerate(BONE_NAMES_DICTIONARY):
        if idx not in [0, 1, 3]:  # 排除ID、根骨骼、头部组
            body_names.extend(list(bone_group))
    
    # 手指骨骼名称（从CSV字典提取）
    finger_names = []
    for finger_group in FINGER_BONE_NAMES_DICTIONARY:
        finger_names.extend(list(finger_group))
    
    # 2. 从IK约束提取IK骨骼
    ik_names = []
    bpy.ops.object.mode_set(mode='POSE')
    for pose_bone in armature_object.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.type == "IK" and constraint.subtarget:
                if constraint.subtarget not in ik_names:
                    ik_names.append(constraint.subtarget)
    
    # 3. 创建预定义面板组
    bpy.context.view_layer.objects.active = root
    for group_en, group_jp in My_Display_Panel_Groups:
        if group_jp not in [f.name for f in root.mmd_root.display_item_frames]:
            new_frame = root.mmd_root.display_item_frames.add()
            new_frame.name = group_jp
            new_frame.name_e = group_en
    
    # 4. 按规则分配骨骼到面板组
    # 规则1：关键词包含匹配（IK/髪/頭/スカト）
    rule1 = [("ＩＫ", ik_names), ("髪", hair_keywords), ("頭", head_keywords), ("スカト", skirt_keywords)]
    for group_jp, keywords in rule1:
        target_frame = next((f for f in root.mmd_root.display_item_frames if f.name == group_jp), None)
        if not target_frame:
            continue
        for bone_name in armature_object.data.bones.keys():
            if bone_name in items_added:
                continue
            if any(keyword in bone_name for keyword in keywords):
                item = __items(target_frame).add()
                item.name = bone_name
                items_added.append(bone_name)
    
    # 规则2：完全匹配（根/指/体）
    rule2 = [("Root", root_names), ("指", finger_names), ("体", body_names)]
    for group_jp, bone_list in rule2:
        target_frame = next((f for f in root.mmd_root.display_item_frames if f.name == group_jp), None)
        if not target_frame:
            continue
        for bone_name in armature_object.data.bones.keys():
            if bone_name in items_added:
                continue
            if bone_name in bone_list:
                item = __items(target_frame).add()
                item.name = bone_name
                items_added.append(bone_name)
    
    # 规则3：未分配骨骼归为Other
    other_frame = next((f for f in root.mmd_root.display_item_frames if f.name == "Other"), None)
    if other_frame:
        for bone_name in armature_object.data.bones.keys():
            if bone_name in items_added:
                continue
            if "dummy" in bone_name.lower() or "shadow" in bone_name.lower():
                continue
            item = __items(other_frame).add()
            item.name = bone_name
            items_added.append(bone_name)

# ------------------------------
# 主执行逻辑
# ------------------------------
def main(context):
    """根据选择的选项，生成/更新显示面板组"""
    # 1. 验证骨架对象
    armature_object = model.findArmature(context.active_object)
    if not armature_object:
        raise Exception("未找到骨架！请选择带有骨架的模型。")
    
    # 2. 获取/创建MMD根对象
    root = model.findRoot(armature_object)
    if not root:
        # 自动转换为MMD模型（若未转换）
        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.mmd_tools.convert_to_mmd_model()
        root = model.findRoot(armature_object)
    if not root:
        raise Exception("创建/查找MMD根对象失败，请手动转换为MMD模型。")
    
    # 3. 获取关联的网格对象
    mesh_objects_list = model.findMeshesList(armature_object)
    if not mesh_objects_list:
        raise Warning("未找到与骨架关联的网格对象，形状键相关功能将跳过。")
    
    # 4. 执行对应生成逻辑
    option = context.scene.display_panel_options
    if option == 'no_change':
        return  # 不修改
    elif option == 'display_panel_groups_from_bone_groups':
        clear_display_panel_groups(root)
        display_panel_groups_from_bone_groups(root, armature_object)
        display_panel_groups_from_shape_keys(mesh_objects_list)
        display_panel_groups_non_vertex_morphs(root)
        delete_empty_display_panel_groups(root)
    elif option == 'add_display_panel_groups':
        clear_display_panel_groups(root)
        display_panel_groups_create(root, armature_object)
        display_panel_groups_from_shape_keys(mesh_objects_list)
        display_panel_groups_non_vertex_morphs(root)
        delete_empty_display_panel_groups(root)

# ------------------------------
# 操作符类（支持撤销+错误反馈）
# ------------------------------
class MmdToolsDisplayPanelGroups(bpy.types.Operator):
    """批量添加骨骼名/形状键名到MMD显示面板组"""
    bl_idname = "object.add_display_panel_groups"
    bl_label = "生成MMD显示面板组"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作
    bl_description = "从骨骼组或自定义规则生成MMD显示面板组"

    @classmethod
    def poll(cls, context):
        """按钮启用条件：有活跃对象且能找到骨架"""
        return (context.active_object is not None 
                and model.findArmature(context.active_object) is not None)

    def execute(self, context):
        try:
            main(context)
            option = context.scene.display_panel_options
            if option == 'no_change':
                self.report({'INFO'}, "未修改显示面板组。")
            else:
                self.report({'INFO'}, f"成功生成显示面板组（方式：{option}）。")
            return {'FINISHED'}
        except Warning as w:
            self.report({'WARNING'}, str(w))
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# ------------------------------
# 注册/注销函数
# ------------------------------
def register():
    register_scene_properties()
    bpy.utils.register_class(MmdToolsDisplayPanelGroupsPanel)
    bpy.utils.register_class(MmdToolsDisplayPanelGroups)

def unregister():
    bpy.utils.unregister_class(MmdToolsDisplayPanelGroupsPanel)
    bpy.utils.unregister_class(MmdToolsDisplayPanelGroups)
    unregister_scene_properties()

if __name__ == "__main__":
    register()