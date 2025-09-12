bl_info = {
    "name": "MMD Bones Renamer Helper",
    "author": "Hogarth-MMD (Adapted for Blender 3.6)",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > mmd_tools_helper",
    "description": "Batch renames armature bones between MMD/3ds Max/Rigify/Sims etc. types",
    "warning": "Requires 'model.py' and 'import_csv.py' in the same folder",
    "category": "MMD Tools",
    "support": "COMMUNITY"
}

import bpy

# --------------------------
# 依赖模块容错导入
# --------------------------
try:
    from . import model
    from . import import_csv
    DEPENDENCIES_LOADED = True
    print("--- MMD Bones Renamer: Dependencies loaded ---")
except ImportError as e:
    DEPENDENCIES_LOADED = False
    MISSING_MODULE = str(e).split("'")[1] if "'" in str(e) else "Unknown"
    print(f"--- MMD Bones Renamer: ERROR - Missing module: {MISSING_MODULE} ---")


# --------------------------
# 辅助工具函数
# --------------------------
def use_international_fonts_display_names_bones():
    """启用国际字体+显示骨骼名称"""
    bpy.context.preferences.system.use_international_fonts = True
    if bpy.context.object and bpy.context.object.type == 'ARMATURE':
        bpy.context.object.data.show_names = True
        print("Enabled international fonts and bone name display")


def unhide_all_armatures():
    """显示所有骨架"""
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE' and (obj.hide_viewport or obj.hide_render):
            obj.hide_viewport = False
            obj.hide_render = False
            print(f"Unhidden armature: {obj.name}")


def print_missing_bone_names():
    """检测并打印缺失骨骼"""
    if not DEPENDENCIES_LOADED:
        print("Cannot check missing bones: Dependencies not loaded")
        return

    missing_bones = []
    try:
        main_bone_dict = import_csv.use_csv_bones_dictionary()
        finger_bone_dict = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        print(f"Failed to load bone dictionaries: {str(e)}")
        return

    if not (main_bone_dict and finger_bone_dict and len(main_bone_dict) > 0 and len(finger_bone_dict) > 0):
        print("Bone dictionaries are empty or invalid")
        return

    target_bone_type = bpy.context.scene.Destination_Armature_Type
    if target_bone_type not in main_bone_dict[0] or target_bone_type not in finger_bone_dict[0]:
        print(f"Target bone type '{target_bone_type}' not found in dictionaries")
        return

    main_idx = main_bone_dict[0].index(target_bone_type)
    finger_idx = finger_bone_dict[0].index(target_bone_type)

    try:
        target_armature = model.findArmature(bpy.context.active_object)
    except Exception as e:
        print(f"Failed to find armature: {str(e)}")
        return

    if not target_armature or target_armature.type != 'ARMATURE':
        print("No valid armature selected")
        return

    # 检查主体骨骼
    for bone_entry in main_bone_dict[1:]:
        target_bone_name = bone_entry[main_idx]
        if (target_bone_name 
            and target_bone_name not in ["", "upper body 2", "上半身2"]
            and target_bone_name not in target_armature.data.bones):
            missing_bones.append(target_bone_name)

    # 检查手指骨骼
    for bone_entry in finger_bone_dict[1:]:
        target_bone_name = bone_entry[finger_idx]
        if (target_bone_name 
            and target_bone_name not in ["", "thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]
            and target_bone_name not in target_armature.data.bones):
            missing_bones.append(target_bone_name)

    # 打印报告
    print("\n" + "="*50)
    print(f"Missing Bones Report (Target: {target_bone_type})")
    print(f"Armature: {target_armature.name}")
    print(f"Total missing bones: {len(missing_bones)}")
    if missing_bones:
        for bone in sorted(missing_bones):
            print(f" - {bone}")
    else:
        print(" ✅ No missing bones")
    print("="*50 + "\n")


# --------------------------
# 核心骨骼重命名函数
# --------------------------
def rename_bones(source_type, target_type, bone_dictionary, is_finger=False):
    """批量重命名骨骼"""
    if not DEPENDENCIES_LOADED:
        print("Cannot rename bones: Dependencies not loaded")
        return

    if not bone_dictionary or len(bone_dictionary) < 2:
        print(f"Invalid {('finger ' if is_finger else '')}bone dictionary")
        return

    dict_headers = bone_dictionary[0]
    if source_type not in dict_headers or target_type not in dict_headers:
        print(f"Source '{source_type}' or Target '{target_type}' not in dictionary")
        return

    source_idx = dict_headers.index(source_type)
    target_idx = dict_headers.index(target_type)

    target_armature = bpy.context.active_object
    if not target_armature or target_armature.type != 'ARMATURE':
        print("Active object is not an armature")
        return

    # 切换到对象模式
    if target_armature.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            print(f"Failed to switch to Object mode: {str(e)}")
            return

    # 执行重命名
    renamed_count = 0
    for bone_entry in bone_dictionary[1:]:
        source_bone = bone_entry[source_idx]
        target_bone = bone_entry[target_idx]

        if source_bone and target_bone and source_bone in target_armature.data.bones:
            if target_armature.data.bones[source_bone].name != target_bone:
                target_armature.data.bones[source_bone].name = target_bone
                renamed_count += 1

                # 同步 MMD 骨骼属性（需安装 mmd_tools）
                if target_type in ['mmd_japanese', 'mmd_japaneseLR']:
                    try:
                        bpy.ops.object.mode_set(mode='POSE')
                        if target_bone in target_armature.pose.bones:
                            pose_bone = target_armature.pose.bones[target_bone]
                            if hasattr(pose_bone, "mmd_bone"):
                                pose_bone.mmd_bone.name_e = bone_entry[0]
                        bpy.ops.object.mode_set(mode='OBJECT')
                    except Exception as e:
                        print(f"Failed to sync mmd_bone: {str(e)}")
                        bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Renamed {renamed_count} {('finger ' if is_finger else '')}bones")


def main():
    """主逻辑"""
    if not DEPENDENCIES_LOADED:
        return {"error": f"Missing dependencies: {MISSING_MODULE}"}

    # 查找骨架
    try:
        target_armature = model.findArmature(bpy.context.active_object)
    except Exception as e:
        return {"error": f"Find armature failed: {str(e)}"}

    if not target_armature:
        return {"error": "No armature associated with selected object"}

    bpy.context.view_layer.objects.active = target_armature
    print(f"Active armature: {target_armature.name}")

    # 辅助设置
    use_international_fonts_display_names_bones()
    unhide_all_armatures()

    # 读取字典
    try:
        main_bones = import_csv.use_csv_bones_dictionary()
        finger_bones = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        return {"error": f"Load bone dictionaries failed: {str(e)}"}

    # 执行重命名
    source_type = bpy.context.scene.Origin_Armature_Type
    target_type = bpy.context.scene.Destination_Armature_Type
    rename_bones(source_type, target_type, main_bones, is_finger=False)
    rename_bones(source_type, target_type, finger_bones, is_finger=True)

    # 检测缺失骨骼
    print_missing_bone_names()

    # 切换到姿态模式
    try:
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
    except Exception as e:
        return {"warning": f"Switch to Pose mode failed: {str(e)}"}

    return {"success": "Bone renaming completed"}


# --------------------------
# UI 面板与操作器
# --------------------------
class BonesRenamerPanel_MTH(bpy.types.Panel):
    bl_label = "MMD Bones Renamer"
    bl_idname = "OBJECT_PT_bones_renamer_MTH"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon="ARMATURE_DATA")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # 依赖缺失提示
        if not DEPENDENCIES_LOADED:
            col.label(text="❌ Missing Dependencies!", icon='ERROR')
            col.label(text=f"Need: {MISSING_MODULE}.py")
            col.label(text="Place in same folder as main script")
            return

        # 源/目标骨骼类型选择
        col.label(text="From Bone Type:", icon='EXPORT')
        col.prop(context.scene, "Origin_Armature_Type", text="")
        col.separator()

        col.label(text="To Bone Type:", icon='IMPORT')
        col.prop(context.scene, "Destination_Armature_Type", text="")
        col.separator()

        # 重命名按钮（仅选中骨架时可用）
        row = col.row()
        row.enabled = (context.active_object and context.active_object.type in ['ARMATURE', 'MESH'])
        row.operator("object.mmd_bones_renamer", text="Batch Rename Bones", icon='FILE_REFRESH')

        # 提示
        col.label(text="ℹ️ Check Console for Missing Bones", icon='INFO')


class MMD_Bones_Renamer(bpy.types.Operator):
    bl_idname = "object.mmd_bones_renamer"
    bl_label = "Batch Rename Bones"
    bl_description = "Rename bones between selected types"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return DEPENDENCIES_LOADED and context.active_object is not None

    def execute(self, context):
        result = main()
        if "error" in result:
            self.report({'ERROR'}, result["error"])
            return {'CANCELLED'}
        elif "warning" in result:
            self.report({'WARNING'}, result["warning"])
        else:
            self.report({'INFO'}, "✅ Bone renaming done! Check console")
        return {'FINISHED'}


# --------------------------
# 场景属性注册
# --------------------------
def register_scene_properties():
    bone_type_items = [
        ('mmd_english', 'MMD English', 'MMD 英文骨骼（Hips/Spine）'),
        ('mmd_japanese', 'MMD Japanese', 'MMD 日文骨骼（骨盤/背骨）'),
        ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MMD 日文（带 .L/.R）'),
        ('xna_lara', 'XNALara', 'XNALara 骨骼'),
        ('daz_poser', 'DAZ/Poser', 'DAZ/Poser 骨骼'),
        ('blender_rigify', 'Blender Rigify', 'Rigify 预绑定骨骼'),
        ('sims_2', 'Sims 2', '模拟人生 2 骨骼'),
        ('motion_builder', 'Motion Builder', 'Motion Builder 骨骼'),
        ('3ds_max', '3ds Max', '3ds Max 标准骨骼'),
        ('bepu', 'Bepu IK', 'Bepu 全身 IK 骨骼'),
        ('project_mirai', 'Project Mirai', '初音未来：未来计划'),
        ('manuel_bastioni_lab', 'Manuel Bastioni Lab', 'MBL 骨骼'),
        ('makehuman_mhx', 'Makehuman MHX', 'MakeHuman MHX 骨骼'),
        ('sims_3', 'Sims 3', '模拟人生 3 骨骼'),
        ('doa5lr', 'DOA5LR', '死或生 5 骨骼'),
        ('Bip_001', 'Bip001', '标准 Bip001（UE/Unity）'),
        ('biped_3ds_max', 'Biped (3DS Max)', '3ds Max Biped'),
        ('biped_sfm', 'Biped (SFM)', 'SFM Biped 骨骼'),
        ('valvebiped', 'ValveBiped', 'Valve 骨骼（TF2/CS:GO）'),
        ('iClone7', 'iClone7', 'iClone7 骨骼')
    ]

    # 源骨骼类型
    bpy.types.Scene.Origin_Armature_Type = bpy.props.EnumProperty(
        items=bone_type_items,
        name="From",
        default='mmd_japanese',
        description="Original bone type of your armature"
    )

    # 目标骨骼类型
    bpy.types.Scene.Destination_Armature_Type = bpy.props.EnumProperty(
        items=bone_type_items,
        name="To",
        default='mmd_english',
        description="Target bone type to rename to"
    )


# --------------------------
# 插件注册/注销
# --------------------------
def register():
    try:
        register_scene_properties()
    except Exception as e:
        print(f"Failed to register properties: {str(e)}")

    try:
        bpy.utils.register_class(BonesRenamerPanel_MTH)
        bpy.utils.register_class(MMD_Bones_Renamer)
        print("✅ MMD Bones Renamer registered (Blender 3.6)")
    except Exception as e:
        print(f"❌ Failed to register classes: {str(e)}")


def unregister():
    try:
        bpy.utils.unregister_class(MMD_Bones_Renamer)
        bpy.utils.unregister_class(BonesRenamerPanel_MTH)
    except Exception as e:
        print(f"Warning: Unregister classes failed: {str(e)}")

    try:
        if hasattr(bpy.types.Scene, "Origin_Armature_Type"):
            del bpy.types.Scene.Origin_Armature_Type
        if hasattr(bpy.types.Scene, "Destination_Armature_Type"):
            del bpy.types.Scene.Destination_Armature_Type
        print("✅ MMD Bones Renamer unregistered")
    except Exception as e:
        print(f"Warning: Delete properties failed: {str(e)}")


if __name__ == "__main__":
    register()