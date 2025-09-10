import bpy
from . import model  # 依赖外部 model 模块（需确保该模块存在）
from . import import_csv  # 依赖外部 CSV 骨骼字典模块（需确保该模块存在）
print("---bonesMaps_renamer---")


# 骨骼重命名面板（显示在 3D 视图右侧属性栏）
class BonesRenamerPanel_MTH(bpy.types.Panel):
    """Creates the Bones Renamer Panel in a VIEW_3D UI tab"""
    bl_label = "Bones Renamer"
    bl_idname = "OBJECT_PT_bones_renamer_MTH"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+ 移除 "TOOLS" 区域，改用右侧 "UI" 区域
    bl_category = "mmd_tools_helper"  # 面板归类到 "mmd_tools_helper" 标签页

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row.label(text="Mass Rename Bones", icon="ARMATURE_DATA")
        row = layout.row()
        row = layout.row()
        
        # 源骨骼类型选择（从场景属性读取）
        layout.prop(context.scene, "Origin_Armature_Type")
        row = layout.row()
        
        # 目标骨骼类型选择（从场景属性读取）
        layout.prop(context.scene, "Destination_Armature_Type")
        row = layout.row()
        
        # 触发重命名的按钮
        row.operator("object.bones_renamer", text="Mass Rename Bones")
        row = layout.row()


# 启用国际字体并显示骨骼名称（适配 Blender 3.6）
def use_international_fonts_display_names_bones():
    # Blender 2.8+ 移除 user_preferences，改用 preferences
    #bpy.context.preferences.system.use_international_fonts = True
    # 确保当前对象是骨架，避免属性不存在错误
    if bpy.context.object and bpy.context.object.type == 'ARMATURE':
        bpy.context.object.data.show_names = True


# 显示所有骨架（修复 Blender 3.6 隐藏属性）
def unhide_all_armatures():
    for o in bpy.context.scene.objects:
        if o.type == 'ARMATURE':
            # Blender 2.8+ 移除 o.hide，拆分为视图隐藏和渲染隐藏
            o.hide_viewport = False  # 视图中显示骨架
            o.hide_render = False    # 渲染时显示骨架


# 打印缺失的骨骼名称（用于调试）
def print_missing_bone_names():
    missing_bone_names = []
    # 从 CSV 模块获取骨骼字典（需确保 CSV 模块正常读取）
    BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
    FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    
    # 容错：避免字典为空导致崩溃
    if not BONE_NAMES_DICTIONARY or not FINGER_BONE_NAMES_DICTIONARY:
        print("Error: Bone dictionary is empty (check CSV import module)")
        return
    
    # 获取目标骨骼映射类型
    SelectedBoneMap = bpy.context.scene.Destination_Armature_Type
    # 容错：检查目标映射是否在字典中
    if SelectedBoneMap not in BONE_NAMES_DICTIONARY[0] or SelectedBoneMap not in FINGER_BONE_NAMES_DICTIONARY[0]:
        print(f"Error: Bone map '{SelectedBoneMap}' not found in dictionary")
        return
    
    # 计算目标骨骼在字典中的索引
    BoneMapIndex = BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
    FingerBoneMapIndex = FINGER_BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
    
    # 找到并激活目标骨架（依赖 model 模块的 findArmature 函数）
    target_armature = model.findArmature(bpy.context.active_object)
    if not target_armature:
        print("Error: No armature found for active object")
        return
    # Blender 2.8+ 活动对象设置改用 view_layer.objects.active
    bpy.context.view_layer.objects.active = target_armature
    
    # 检查主体骨骼是否缺失
    for b in BONE_NAMES_DICTIONARY:
        b_idx = BONE_NAMES_DICTIONARY.index(b)
        if b_idx != 0 and b[BoneMapIndex] != '' and b[BoneMapIndex] not in ["upper body 2", "上半身2"]:
            if b[BoneMapIndex] not in target_armature.data.bones.keys():
                missing_bone_names.append(b[BoneMapIndex])
    
    # 检查手指骨骼是否缺失
    for b in FINGER_BONE_NAMES_DICTIONARY:
        b_idx = FINGER_BONE_NAMES_DICTIONARY.index(b)
        if b_idx != 0 and b[FingerBoneMapIndex] != '' and b[FingerBoneMapIndex] not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]:
            if b[FingerBoneMapIndex] not in target_armature.data.bones.keys():
                missing_bone_names.append(b[FingerBoneMapIndex])
    
    # 打印结果（控制台输出）
    print("\n=== Missing Bones Report ===")
    print(f"Destination bone map: {SelectedBoneMap}")
    print(f"Missing bones in active armature:")
    if missing_bone_names:
        for bone in missing_bone_names:
            print(f"- {bone}")
    else:
        print("None (all required bones exist)")
    print("===========================")


# 重命名主体骨骼（核心功能）
def rename_bones(boneMap1, boneMap2, BONE_NAMES_DICTIONARY): 
    # 容错：避免字典为空
    if not BONE_NAMES_DICTIONARY:
        print("Error: Main bone dictionary is empty")
        return
    
    boneMaps = BONE_NAMES_DICTIONARY[0]
    # 容错：检查源/目标映射是否有效
    if boneMap1 not in boneMaps or boneMap2 not in boneMaps:
        print(f"Error: Bone map '{boneMap1}' (source) or '{boneMap2}' (target) not found")
        return
    
    # 获取源/目标骨骼在字典中的索引
    boneMap1_index = boneMaps.index(boneMap1)
    boneMap2_index = boneMaps.index(boneMap2)
    
    # 切换到对象模式（避免编辑/姿态模式下的重命名错误）
    if bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 确认当前对象是骨架
    target_armature = bpy.context.active_object
    if target_armature.type != 'ARMATURE':
        print("Error: Active object is not an armature")
        return
    
    # 遍历字典并重命名骨骼
    for k in BONE_NAMES_DICTIONARY[1:]:
        src_bone_name = k[boneMap1_index]  # 源骨骼名称
        dst_bone_name = k[boneMap2_index]  # 目标骨骼名称
        # 仅当源骨骼存在且目标名称非空时重命名
        if src_bone_name in target_armature.data.bones.keys() and dst_bone_name != '':
            target_armature.data.bones[src_bone_name].name = dst_bone_name
            # 若目标是 MMD 日语骨骼，同步 mmd_bone 属性（需安装 mmd_tools 插件）
            if boneMap2 in ['mmd_japanese', 'mmd_japaneseLR']:
                bpy.ops.object.mode_set(mode='POSE')
                if dst_bone_name in target_armature.pose.bones and hasattr(target_armature.pose.bones[dst_bone_name], "mmd_bone"):
                    target_armature.pose.bones[dst_bone_name].mmd_bone.name_e = k[0]
                bpy.ops.object.mode_set(mode='OBJECT')


# 重命名手指骨骼（核心功能）
def rename_finger_bones(boneMap1, boneMap2, FINGER_BONE_NAMES_DICTIONARY):
    # 容错：避免字典为空
    if not FINGER_BONE_NAMES_DICTIONARY:
        print("Error: Finger bone dictionary is empty")
        return
    
    boneMaps = FINGER_BONE_NAMES_DICTIONARY[0]
    # 容错：检查源/目标映射是否有效
    if boneMap1 not in boneMaps or boneMap2 not in boneMaps:
        print(f"Error: Finger bone map '{boneMap1}' (source) or '{boneMap2}' (target) not found")
        return
    
    # 获取源/目标骨骼在字典中的索引
    boneMap1_index = boneMaps.index(boneMap1)
    boneMap2_index = boneMaps.index(boneMap2)
    
    # 切换到对象模式
    if bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 确认当前对象是骨架
    target_armature = bpy.context.active_object
    if target_armature.type != 'ARMATURE':
        print("Error: Active object is not an armature")
        return
    
    # 遍历手指骨骼字典并重命名
    for k in FINGER_BONE_NAMES_DICTIONARY[1:]:
        src_bone_name = k[boneMap1_index]  # 源手指骨骼名称
        dst_bone_name = k[boneMap2_index]  # 目标手指骨骼名称
        # 仅当源骨骼存在且目标名称非空时重命名
        if src_bone_name in target_armature.data.bones.keys() and dst_bone_name != '':
            target_armature.data.bones[src_bone_name].name = dst_bone_name
            # 若目标是 MMD 日语骨骼，同步 mmd_bone 属性
            if boneMap2 in ['mmd_japanese', 'mmd_japaneseLR']:
                bpy.ops.object.mode_set(mode='POSE')
                if dst_bone_name in target_armature.pose.bones and hasattr(target_armature.pose.bones[dst_bone_name], "mmd_bone"):
                    target_armature.pose.bones[dst_bone_name].mmd_bone.name_e = k[0]
                bpy.ops.object.mode_set(mode='OBJECT')
    
    # 更新源骨骼类型为当前目标类型（方便后续二次重命名）
    bpy.context.scene.Origin_Armature_Type = boneMap2
    # 打印缺失骨骼报告
    print_missing_bone_names()


# 主逻辑函数（串联所有功能）
def main(context):
    # 1. 找到并激活目标骨架（依赖 model 模块的 findArmature 函数）
    target_armature = model.findArmature(bpy.context.active_object)
    if not target_armature:
        print("Error: No armature associated with active object")
        return
    bpy.context.view_layer.objects.active = target_armature
    
    # 2. 启用国际字体 + 显示骨骼名称
    use_international_fonts_display_names_bones()
    
    # 3. 显示所有骨架（避免隐藏导致的重命名遗漏）
    unhide_all_armatures()
    
    # 4. 从 CSV 模块获取骨骼字典
    BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
    FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    
    # 5. 执行主体骨骼重命名
    rename_bones(
        bpy.context.scene.Origin_Armature_Type,  # 源骨骼类型（用户选择）
        bpy.context.scene.Destination_Armature_Type,  # 目标骨骼类型（用户选择）
        BONE_NAMES_DICTIONARY
    )
    
    # 6. 执行手指骨骼重命名
    rename_finger_bones(
        bpy.context.scene.Origin_Armature_Type,
        bpy.context.scene.Destination_Armature_Type,
        FINGER_BONE_NAMES_DICTIONARY
    )
    
    # 7. 切换到姿态模式并全选骨骼（方便后续操作）
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')


# 骨骼重命名操作器（点击按钮触发）
class BonesRenamer(bpy.types.Operator):
    """Mass bones renamer for armature conversion (supports Blender 3.6)"""
    bl_idname = "object.bones_renamer"
    bl_label = "Bones Renamer"
    bl_options = {'REGISTER', 'UNDO'}  # 支持 Blender 撤销功能（3.6 必需显式声明）

    def execute(self, context):
        # 前置检查：确保有活动对象
        if not bpy.context.active_object:
            self.report({'ERROR'}, "No active object found! Please select a model/armature first.")
            return {'CANCELLED'}
        
        # 前置检查：确保活动对象关联骨架（依赖 model 模块）
        if not model.findArmature(bpy.context.active_object):
            self.report({'ERROR'}, "No armature found for the selected object!")
            return {'CANCELLED'}
        
        # 执行主逻辑
        main(context)
        self.report({'INFO'}, "Bone renaming completed! Check console for missing bones report.")
        return {'FINISHED'}


# 注册场景属性（源/目标骨骼类型枚举，Blender 3.6 需单独注册）
def register_scene_properties():
    # 1. 源骨骼类型枚举（用户选择“从哪种骨骼类型开始重命名”）
    bpy.types.Scene.Origin_Armature_Type = bpy.props.EnumProperty(
        items=[
            ('mmd_english', 'MMD English', 'MikuMikuDance English bone names'),
            ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bone names'),
            ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MMD Japanese bones with .L/.R suffixes'),
            ('xna_lara', 'XNALara', 'XNALara bone names'),
            ('daz_poser', 'DAZ/Poser', 'DAZ/Poser/Second Life bone names'),
            ('blender_rigify', 'Blender Rigify', 'Blender Rigify pre-rig bone names'),
            ('sims_2', 'Sims 2', 'Sims 2 bone names'),
            ('motion_builder', 'Motion Builder', 'Motion Builder bone names'),
            ('3ds_max', '3ds Max', '3ds Max bone names'),
            ('bepu', 'Bepu IK', 'Bepu full body IK bone names'),
            ('project_mirai', 'Project Mirai', 'Project Mirai bone names'),
            ('manuel_bastioni_lab', 'Manuel Bastioni Lab', 'Manuel Bastioni Lab bone names'),
            ('makehuman_mhx', 'Makehuman MHX', 'Makehuman MHX bone names'),
            ('sims_3', 'Sims 3', 'Sims 3 bone names'),
            ('doa5lr', 'DOA5LR', 'Dead or Alive 5 Last Round bone names'),
            ('Bip_001', 'Bip001', 'Bip001 standard bone names'),
            ('biped_3ds_max', 'Biped (3DS Max)', '3DS Max Biped bone names'),
            ('biped_sfm', 'Biped (SFM)', 'Source Film Maker Biped bone names'),
            ('valvebiped', 'ValveBiped', 'ValveBiped (e.g. TF2) bone names'),
            ('iClone7', 'iClone7', 'iClone7 bone names')
        ],
        name="From Bone Type",  # UI 显示的标签
        default='mmd_japanese'  # 默认选择 MMD 日语骨骼
    )

    # 2. 目标骨骼类型枚举（用户选择“重命名到哪种骨骼类型”）
    bpy.types.Scene.Destination_Armature_Type = bpy.props.EnumProperty(
        items=[
            ('mmd_english', 'MMD English', 'MikuMikuDance English bone names'),
            ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bone names'),
            ('mmd_japaneseLR', 'MMD Japanese (.L.R)', 'MMD Japanese bones with .L/.R suffixes'),
            ('xna_lara', 'XNALara', 'XNALara bone names'),
            ('daz_poser', 'DAZ/Poser', 'DAZ/Poser/Second Life bone names'),
            ('blender_rigify', 'Blender Rigify', 'Blender Rigify pre-rig bone names'),
            ('sims_2', 'Sims 2', 'Sims 2 bone names'),
            ('motion_builder', 'Motion Builder', 'Motion Builder bone names'),
            ('3ds_max', '3ds Max', '3ds Max bone names'),
            ('bepu', 'Bepu IK', 'Bepu full body IK bone names'),
            ('project_mirai', 'Project Mirai', 'Project Mirai bone names'),
            ('manuel_bastioni_lab', 'Manuel Bastioni Lab', 'Manuel Bastioni Lab bone names'),
            ('makehuman_mhx', 'Makehuman MHX', 'Makehuman MHX bone names'),
            ('sims_3', 'Sims 3', 'Sims 3 bone names'),
            ('doa5lr', 'DOA5LR', 'Dead or Alive 5 Last Round bone names'),
            ('Bip_001', 'Bip001', 'Bip001 standard bone names'),
            ('biped_3ds_max', 'Biped (3DS Max)', '3DS Max Biped bone names'),
            ('biped_sfm', 'Biped (SFM)', 'Source Film Maker Biped bone names'),
            ('valvebiped', 'ValveBiped', 'ValveBiped (e.g. TF2) bone names'),
            ('iClone7', 'iClone7', 'iClone7 bone names')
        ],
        name="To Bone Type",  # UI 显示的标签
        default='mmd_english'  # 默认目标为 MMD 英语骨骼
    )


# 注册函数（Blender 插件必需的注册逻辑）
def register():
    # 1. 先注册场景属性（避免面板读取属性时报错）
    register_scene_properties()
    # 2. 注册面板和操作器
    bpy.utils.register_class(BonesRenamerPanel_MTH)
    bpy.utils.register_class(BonesRenamer)
    print("Bones Renamer tool registered (Blender 3.6 compatible)")


# 注销函数（插件卸载时清理）
def unregister():
    # 1. 注销操作器和面板
    bpy.utils.unregister_class(BonesRenamer)
    bpy.utils.unregister_class(BonesRenamerPanel_MTH)
    # 2. 移除场景属性（避免残留）
    del bpy.types.Scene.Origin_Armature_Type
    del bpy.types.Scene.Destination_Armature_Type
    print("Bones Renamer tool unregistered")


# 直接运行时注册（用于测试）
if __name__ == "__main__":
    register()
register()   