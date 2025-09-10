import bpy
# 确保import_csv和model模块存在（通常来自mmd_tools插件）
print("armature_diagnostic---->")
try:
    from . import import_csv
    from . import model
except ImportError:
    raise ImportError("请确保已安装mmd_tools插件及其依赖模块")


class ArmatureDiagnosticPanel(bpy.types.Panel):
    """骨架诊断面板"""
    bl_label = "Armature Diagnostic Panel"
    bl_idname = "OBJECT_PT_armature_diagnostic"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 关键修改：Blender 2.8+使用UI区域替代TOOLS
    bl_category = "mmd_tools_helper"  # 在N面板中的分类
    bl_order = 12  # 排序，确保在其他mmd工具面板之后


    def draw(self, context):
        layout = self.layout
        
        # 骨架类型选择下拉菜单
        layout.prop(context.scene, "selected_armature_to_diagnose")
        
        # 诊断按钮
        layout.operator("mmd_tools_helper.armature_diagnostic", 
                      text="Diagnose Armature", 
                      icon='ARMATURE_DATA')
        
        # 空行占位
        layout.separator()


def main(context):
    """主诊断逻辑：检查骨架中缺失的骨骼"""
    missing_bone_names = []
    
    # 获取骨骼名称字典（从CSV文件）
    try:
        BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        raise RuntimeError(f"无法加载骨骼字典: {str(e)}")
    
    # 获取选中的骨架类型
    selected_bone_map = context.scene.selected_armature_to_diagnose
    
    # 查找字典索引
    try:
        bone_map_index = BONE_NAMES_DICTIONARY[0].index(selected_bone_map)
        finger_bone_map_index = FINGER_BONE_NAMES_DICTIONARY[0].index(selected_bone_map)
    except ValueError:
        raise ValueError(f"在骨骼字典中未找到 {selected_bone_map}")
    
    # 获取并激活骨架
    armature = model.findArmature(context.active_object)
    if not armature:
        raise ValueError("未找到关联的骨架对象")
    context.view_layer.objects.active = armature  # 替代废弃的scene.objects.active
    armature_data = armature.data
    existing_bones = armature_data.bones.keys()
    
    # 检查主要骨骼
    for bone_entry in BONE_NAMES_DICTIONARY[1:]:  # 跳过表头
        bone_name = bone_entry[bone_map_index]
        if bone_name and bone_name not in ["upper body 2", "上半身2"]:
            if bone_name not in existing_bones:
                missing_bone_names.append(bone_name)
    
    # 检查手指骨骼
    for finger_entry in FINGER_BONE_NAMES_DICTIONARY[1:]:  # 跳过表头
        bone_name = finger_entry[finger_bone_map_index]
        if bone_name and bone_name not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"]:
            if bone_name not in existing_bones:
                missing_bone_names.append(bone_name)
    
    # 输出诊断结果
    print("\n" + "="*50)
    print(f"选中的骨骼映射类型: {selected_bone_map}")
    print(f"该骨架缺失的{selected_bone_map}骨骼:")
    for bone in missing_bone_names:
        print(f"- {bone}")
    
    # MMD英文骨架特殊说明
    if selected_bone_map == 'mmd_english':
        print("\n注意：以下3种骨骼是MMD半标准骨骼，并非必需：")
        print("upper body 2, thumb0_L, thumb0_R")
    print("="*50 + "\n")


class ArmatureDiagnostic(bpy.types.Operator):
    """诊断骨架缺失的骨骼"""
    bl_idname = "mmd_tools_helper.armature_diagnostic"
    bl_label = "Armature Diagnostic"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作


    @classmethod
    def poll(cls, context):
        """仅当选中有效对象时启用按钮"""
        return context.active_object is not None


    def execute(self, context):
        """执行诊断操作"""
        try:
            # 获取并激活骨架
            armature = model.findArmature(context.active_object)
            if not armature:
                self.report({'ERROR'}, "未找到关联的骨架")
                return {'CANCELLED'}
            
            # 打印所有骨骼名称（排除dummy和shadow骨骼）
            print("\n" + "="*50)
            print(f"{armature.name} 的所有骨骼名称:")
            all_bones = [b for b in armature.data.bones.keys() 
                        if 'dummy' not in b.lower() and 'shadow' not in b.lower()]
            for bone in all_bones:
                print(f"- {bone}")
            print("="*50 + "\n")
            
            # 执行主诊断逻辑
            main(context)
            self.report({'INFO'}, "骨架诊断完成，结果已输出到控制台")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"诊断失败: {str(e)}")
            return {'CANCELLED'}


# 定义骨架类型枚举属性（在类外部定义，适配Blender 3.6）
bpy.types.Scene.selected_armature_to_diagnose = bpy.props.EnumProperty(
    items=[
        ('mmd_english', 'MMD English', 'MikuMikuDance English bone names'),
        ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bone names'),
        ('mmd_japaneseLR', 'MMD Japanese .L.R', 'MMD Japanese with .L.R suffixes'),
        ('xna_lara', 'XNALara', 'XNALara bone names'),
        ('daz_poser', 'DAZ/Poser', 'DAZ/Poser bone names'),
        ('blender_rigify', 'Blender Rigify', 'Blender rigify bone names'),
        ('sims_2', 'Sims 2', 'Sims 2 bone names'),
        ('motion_builder', 'Motion Builder', 'Motion Builder bone names'),
        ('3ds_max', '3ds Max', '3ds Max bone names'),
        ('bepu', 'Bepu IK', 'Bepu full body IK bone names'),
        ('project_mirai', 'Project Mirai', 'Project Mirai bone names'),
        ('manuel_bastioni_lab', 'Manuel Bastioni', 'Manuel Bastioni Lab bone names'),
        ('makehuman_mhx', 'MakeHuman MHX', 'Makehuman MHX bone names'),
        ('sims_3', 'Sims 3', 'Sims 3 bone names'),
        ('doa5lr', 'DOA5LR', 'Dead or Alive 5 Last Round bone names'),
        ('Bip_001', 'Bip001', 'Bip001 bone names'),
        ('biped_3ds_max', '3DS Max Biped', 'Biped 3DS Max bone names'),
        ('biped_sfm', 'SFM Biped', 'Source Film Maker bone names'),
        ('valvebiped', 'ValveBiped', 'ValveBiped bone names'),
        ('iClone7', 'iClone7', 'iClone7 bone names')
    ],
    name="Armature Type",
    default='mmd_english'
)


def register():
    """注册插件类"""
    bpy.utils.register_class(ArmatureDiagnosticPanel)
    bpy.utils.register_class(ArmatureDiagnostic)


def unregister():
    """反注册插件类"""
    bpy.utils.unregister_class(ArmatureDiagnosticPanel)
    bpy.utils.unregister_class(ArmatureDiagnostic)
    # 清理属性定义
    del bpy.types.Scene.selected_armature_to_diagnose


if __name__ == "__main__":
    register()
register()