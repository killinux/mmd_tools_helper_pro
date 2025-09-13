import bpy
from . import model  # 确保同目录下有 model.py 模块（含 findArmature 函数）
from . import import_csv  # 确保同目录下有 import_csv.py 模块

print("---bonesMaps_renamer--->>")


# ------------------------------
# 1. 面板类（适配 Blender 3.6 UI）
# ------------------------------
class BonesRenamerPanel_MTH(bpy.types.Panel):
    """在 3D 视图侧边栏创建骨骼重命名面板"""
    bl_label = "Bones Renamer"
    bl_idname = "OBJECT_PT_bones_renamer_MTH"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"  # 侧边栏标签（无则手动创建）
    bl_context = "objectmode"  # 仅物体模式显示

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view_layer = scene.view_layers[0]  # 从视图层获取活跃对象

        # 标题与分隔符
        layout.row().label(text="Mass Rename Bones", icon="ARMATURE_DATA")
        layout.separator()

        # 骨骼类型选择
        layout.prop(scene, "Origin_Armature_Type", text="From")
        layout.prop(scene, "Destination_Armature_Type", text="To")
        layout.separator()

        # 重命名按钮（仅选中骨架时可用）
        row = layout.row()
        row.operator("object.bones_renamer", text="Mass Rename Bones")
        row.enabled = bool(view_layer.objects.active and view_layer.objects.active.type == "ARMATURE")


# ------------------------------
# 2. 辅助函数（移除 use_international_fonts）
# ------------------------------
def enable_bone_names_display():
    """仅保留“显示骨骼名称”功能（移除废弃的国际字体属性）"""
    scene = bpy.context.scene
    view_layer = scene.view_layers[0]
    active_obj = view_layer.objects.active

    # 若选中骨架，启用骨骼名称显示
    if active_obj and active_obj.type == "ARMATURE":
        active_obj.data.show_names = True  # 核心功能：在视图中显示骨骼名称
        print("已启用骨骼名称显示")
    else:
        print("警告：未选中骨架对象，无法启用骨骼名称显示")


def unhide_all_armatures():
    """显示场景中所有骨架对象"""
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            obj.hide_viewport = False  # 视图中显示
            obj.hide_select = False    # 允许选中


def print_missing_bone_names():
    """打印目标骨骼类型中缺失的骨骼"""
    missing_bone_names = []
    scene = bpy.context.scene
    view_layer = scene.view_layers[0]
    active_obj = view_layer.objects.active

    # 读取CSV字典（容错处理）
    try:
        bone_dict = import_csv.use_csv_bones_dictionary()
        finger_bone_dict = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        print(f"读取骨骼字典失败：{str(e)}")
        return

    # 验证字典格式
    if not (isinstance(bone_dict, list) and len(bone_dict) > 0):
        print("错误：普通骨骼字典格式无效")
        return
    if not (isinstance(finger_bone_dict, list) and len(finger_bone_dict) > 0):
        print("错误：手指骨骼字典格式无效")
        return

    # 获取目标骨骼类型及索引
    target_bone_type = scene.Destination_Armature_Type
    try:
        bone_type_idx = bone_dict[0].index(target_bone_type)
        finger_type_idx = finger_bone_dict[0].index(target_bone_type)
    except ValueError:
        print(f"错误：目标骨骼类型「{target_bone_type}」不在字典中")
        return

    # 找到并激活骨架对象
    armature_obj = model.findArmature(active_obj)
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("错误：未找到有效骨架对象")
        return
    view_layer.objects.active = armature_obj  # 激活骨架

    # 检查普通骨骼缺失
    for bone_entry in bone_dict[1:]:  # 跳过首行（骨骼类型列表）
        if len(bone_entry) <= bone_type_idx:
            continue
        target_bone = bone_entry[bone_type_idx]
        if (target_bone != "" 
            and target_bone not in ["upper body 2", "上半身2"]
            and target_bone not in armature_obj.data.bones):
            missing_bone_names.append(target_bone)

    # 检查手指骨骼缺失
    for finger_entry in finger_bone_dict[1:]:
        if len(finger_entry) <= finger_type_idx:
            continue
        target_finger = finger_entry[finger_type_idx]
        if (target_finger != ""
            and target_finger not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]
            and target_finger not in armature_obj.data.bones):
            missing_bone_names.append(target_finger)

    # 打印结果
    print(f"\n目标骨骼类型：{target_bone_type}")
    print(f"缺失的骨骼：{missing_bone_names if missing_bone_names else '无'}")


def rename_bones(source_type, target_type, bone_dict):
    """重命名普通骨骼"""
    scene = bpy.context.scene
    view_layer = scene.view_layers[0]
    armature_obj = view_layer.objects.active

    # 验证输入
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("错误：未激活骨架对象")
        return
    if not (isinstance(bone_dict, list) and len(bone_dict) > 0):
        print("错误：骨骼字典格式无效")
        return

    # 获取骨骼类型索引
    try:
        source_idx = bone_dict[0].index(source_type)
        target_idx = bone_dict[0].index(target_type)
    except ValueError:
        print(f"错误：骨骼类型「{source_type}」或「{target_type}」不在字典中")
        return

    # 切换到物体模式（确保可编辑骨骼）
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        print("警告：无法切换到物体模式")
        return

    # 执行重命名
    for bone_entry in bone_dict[1:]:
        if len(bone_entry) <= max(source_idx, target_idx):
            continue
        source_bone = bone_entry[source_idx]
        target_bone = bone_entry[target_idx]

        if (source_bone != "" 
            and target_bone != "" 
            and source_bone in armature_obj.data.bones):
            armature_obj.data.bones[source_bone].name = target_bone
            print(f"重命名：{source_bone} → {target_bone}")

            # 同步MMD骨骼属性（依赖 mmd_tools 插件）
            if target_type in ["mmd_japanese", "mmd_japaneseLR"]:
                try:
                    bpy.ops.object.mode_set(mode="POSE")
                    pose_bone = armature_obj.pose.bones.get(target_bone)
                    if pose_bone and hasattr(pose_bone, "mmd_bone"):
                        pose_bone.mmd_bone.name_e = bone_entry[0]
                    bpy.ops.object.mode_set(mode="OBJECT")
                except (RuntimeError, AttributeError):
                    print(f"警告：无法同步MMD属性（{target_bone}）")


def rename_finger_bones(source_type, target_type, finger_dict):
    """重命名手指骨骼"""
    scene = bpy.context.scene
    view_layer = scene.view_layers[0]
    armature_obj = view_layer.objects.active

    # 验证输入
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("错误：未激活骨架对象")
        return
    if not (isinstance(finger_dict, list) and len(finger_dict) > 0):
        print("错误：手指骨骼字典格式无效")
        return

    # 获取骨骼类型索引
    try:
        source_idx = finger_dict[0].index(source_type)
        target_idx = finger_dict[0].index(target_type)
    except ValueError:
        print(f"错误：手指骨骼类型「{source_type}」或「{target_type}」不在字典中")
        return

    # 切换到物体模式
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        print("警告：无法切换到物体模式")
        return

    # 执行重命名
    for finger_entry in finger_dict[1:]:
        if len(finger_entry) <= max(source_idx, target_idx):
            continue
        source_bone = finger_entry[source_idx]
        target_bone = finger_entry[target_idx]

        if (source_bone != "" 
            and target_bone != "" 
            and source_bone in armature_obj.data.bones):
            armature_obj.data.bones[source_bone].name = target_bone
            print(f"重命名手指：{source_bone} → {target_bone}")

            # 同步MMD属性
            if target_type in ["mmd_japanese", "mmd_japaneseLR"]:
                try:
                    bpy.ops.object.mode_set(mode="POSE")
                    pose_bone = armature_obj.pose.bones.get(target_bone)
                    if pose_bone and hasattr(pose_bone, "mmd_bone"):
                        pose_bone.mmd_bone.name_e = finger_entry[0]
                    bpy.ops.object.mode_set(mode="OBJECT")
                except (RuntimeError, AttributeError):
                    print(f"警告：无法同步MMD属性（手指骨骼 {target_bone}）")

    # 更新源类型并检查缺失骨骼
    scene.Origin_Armature_Type = target_type
    print_missing_bone_names()


# ------------------------------
# 3. 主逻辑函数
# ------------------------------
def main(context):
    scene = context.scene
    view_layer = scene.view_layers[0]
    active_obj = view_layer.objects.active

    # 找到并激活骨架
    armature_obj = model.findArmature(active_obj)
    if not (armature_obj and armature_obj.type == "ARMATURE"):
        print("错误：未找到有效骨架对象")
        return
    view_layer.objects.active = armature_obj

    # 执行核心操作（移除国际字体相关代码）
    enable_bone_names_display()  # 仅显示骨骼名称
    unhide_all_armatures()

    # 读取骨骼字典
    try:
        bone_dict = import_csv.use_csv_bones_dictionary()
        finger_dict = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        print(f"读取字典失败：{str(e)}")
        return

    # 重命名骨骼
    rename_bones(
        scene.Origin_Armature_Type,
        scene.Destination_Armature_Type,
        bone_dict
    )
    rename_finger_bones(
        scene.Origin_Armature_Type,
        scene.Destination_Armature_Type,
        finger_dict
    )

    # 切换到姿态模式并全选骨骼
    try:
        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="SELECT")
    except RuntimeError:
        print("警告：无法切换到姿态模式或全选骨骼")


# ------------------------------
# 4. 操作器类（按钮逻辑）
# ------------------------------
class BonesRenamer(bpy.types.Operator):
    bl_idname = "object.bones_renamer"
    bl_label = "Bones Renamer"
    bl_options = {"REGISTER", "UNDO"}  # 支持撤销

    @classmethod
    def poll(cls, context):
        """仅当选中骨架时可点击"""
        view_layer = context.scene.view_layers[0]
        return bool(view_layer.objects.active and view_layer.objects.active.type == "ARMATURE")

    def execute(self, context):
        main(context)
        self.report({"INFO"}, "骨骼重命名完成（查看控制台日志）")
        return {"FINISHED"}


# ------------------------------
# 5. 注册场景属性（骨骼类型枚举）
# ------------------------------
def register_scene_properties():
    bone_type_items = [
        ('mmd_english', 'MMD English', 'MikuMikuDance English bones'),
        ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bones'),
        ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MMD Japanese with .L.R suffix'),
        ('xna_lara', 'XNALara', 'XNALara bones'),
        ('daz_poser', 'DAZ/Poser', 'DAZ/Poser/Second Life bones'),
        ('blender_rigify', 'Blender Rigify', 'Rigify pre-rig bones'),
        ('sims_2', 'Sims 2', 'Sims 2 bones'),
        ('motion_builder', 'Motion Builder', 'Motion Builder bones'),
        ('3ds_max', '3ds Max', '3ds Max bones'),
        ('bepu', 'Bepu Full-Body IK', 'Bepu IK bones'),
        ('project_mirai', 'Project Mirai', 'Project Mirai bones'),
        ('manuel_bastioni_lab', 'Manuel Bastioni Lab', 'MBL bones'),
        ('makehuman_mhx', 'MakeHuman MHX', 'MakeHuman MHX bones'),
        ('sims_3', 'Sims 3', 'Sims 3 bones'),
        ('doa5lr', 'DOA5LR', 'Dead or Alive 5 LR bones'),
        ('Bip_001', 'Bip001', 'Bip001 bones'),
        ('biped_3ds_max', 'Biped (3ds Max)', '3ds Max Biped bones'),
        ('biped_sfm', 'Biped (SFM)', 'Source Film Maker Biped bones'),
        ('valvebiped', 'ValveBiped', 'ValveBiped bones'),
        ('iClone7', 'iClone 7', 'iClone7 bones')
    ]

    # 源骨骼类型
    bpy.types.Scene.Origin_Armature_Type = bpy.props.EnumProperty(
        items=bone_type_items,
        name="Rename From",
        default='mmd_japanese'
    )

    # 目标骨骼类型
    bpy.types.Scene.Destination_Armature_Type = bpy.props.EnumProperty(
        items=bone_type_items,
        name="Rename To",
        default='mmd_english'
    )


def unregister_scene_properties():
    del bpy.types.Scene.Origin_Armature_Type
    del bpy.types.Scene.Destination_Armature_Type


# ------------------------------
# 6. 注册/注销入口
# ------------------------------
def register():
    register_scene_properties()
    bpy.utils.register_class(BonesRenamerPanel_MTH)
    bpy.utils.register_class(BonesRenamer)
    print("Bones Renamer 注册完成")


def unregister():
    bpy.utils.unregister_class(BonesRenamerPanel_MTH)
    bpy.utils.unregister_class(BonesRenamer)
    unregister_scene_properties()
    print("Bones Renamer 注销完成")


if __name__ == "__main__":
    register()