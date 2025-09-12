import bpy
from . import model

print("miscellaneous_tools.py-->")
class MiscellaneousToolsPanel(bpy.types.Panel):
    """Miscellaneous Tools panel"""
    bl_label = "Miscellaneous Tools Panel"
    bl_idname = "OBJECT_PT_miscellaneous_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+ 中使用UI替代TOOLS
    bl_category = "mmd_tools_helper"  # 在N面板中显示的类别

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        layout.prop(context.scene, "selected_miscellaneous_tools")
        row = layout.row()
        row.label(text="Miscellaneous Tools", icon='WORLD_DATA')
        row = layout.row()
        row.operator("mmd_tools_helper.miscellaneous_tools", text="Execute Function")


def all_materials_mmd_ambient_white():
    for m in bpy.data.materials:
        if "mmd_tools_rigid" not in m.name:
            # 修复赋值错误，将==改为=
            m.mmd_material.ambient_color[0] = 1.0
            m.mmd_material.ambient_color[1] = 1.0
            m.mmd_material.ambient_color[2] = 1.0


def combine_2_bones_1_bone(parent_bone_name, child_bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    # 获取活动对象的数据
    armature_data = bpy.context.active_object.data
    child_bone_tail = armature_data.edit_bones[child_bone_name].tail
    armature_data.edit_bones[parent_bone_name].tail = child_bone_tail
    armature_data.edit_bones.remove(armature_data.edit_bones[child_bone_name])
    bpy.ops.object.mode_set(mode='POSE')
    print(f"Combined 2 bones: {parent_bone_name}, {child_bone_name}")


def combine_2_vg_1_vg(parent_vg_name, child_vg_name):
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            if parent_vg_name in o.vertex_groups:
                if child_vg_name in o.vertex_groups:
                    # 遍历所有顶点
                    for v in o.data.vertices:
                        for g in v.groups:
                            if o.vertex_groups[g.group].name == child_vg_name:
                                weight = o.vertex_groups[child_vg_name].weight(v.index)
                                o.vertex_groups[parent_vg_name].add([v.index], weight, 'ADD')
                    # 删除子顶点组
                    o.vertex_groups.remove(o.vertex_groups[child_vg_name])
                    print(f"Combined 2 vertex groups: {parent_vg_name}, {child_vg_name}")


def analyze_selected_parent_child_bone_pair():
    selected_bones = []
    active_obj = bpy.context.active_object
    
    if active_obj and active_obj.type == 'ARMATURE':
        # 在POSE模式下获取选中的骨骼
        for b in active_obj.pose.bones:
            if b.bone.select:
                selected_bones.append(b.bone.name)

    if len(selected_bones) != 2:
        print(f"Exactly 2 bones must be selected. {len(selected_bones)} are selected.")
        return None, None
    
    # 检查父子关系
    armature_data = active_obj.data
    bone1, bone2 = selected_bones[0], selected_bones[1]
    
    if armature_data.bones[bone1].parent == armature_data.bones[bone2]:
        return bone2, bone1  # bone2是父骨骼，bone1是子骨骼
    elif armature_data.bones[bone2].parent == armature_data.bones[bone1]:
        return bone1, bone2  # bone1是父骨骼，bone2是子骨骼
    else:
        print("Selected bones have no parent-child relationship.")
        return None, None


def delete_unused_bones():
    print('\n')
    active_obj = bpy.context.active_object
    
    if not active_obj or active_obj.type != 'ARMATURE':
        print("Active object is not an armature.")
        return
        
    bpy.ops.object.mode_set(mode='EDIT')
    bones_to_delete = []
    
    for b in active_obj.data.edit_bones:
        if 'unused' in b.name.lower():
            bones_to_delete.append(b.name)
    
    for b_name in bones_to_delete:
        if b_name in active_obj.data.edit_bones:
            active_obj.data.edit_bones.remove(active_obj.data.edit_bones[b_name])
            print(f"Removed bone: {b_name}")
    
    bpy.ops.object.mode_set(mode='POSE')


def delete_unused_vertex_groups():
    print('\n')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            delete_these = [vg.name for vg in o.vertex_groups if 'unused' in vg.name.lower()]
            for vg_name in delete_these:
                if vg_name in o.vertex_groups:
                    o.vertex_groups.remove(o.vertex_groups[vg_name])
                    print(f'Removed vertex group: {vg_name}')


def test_is_mmd_english_armature():
    mmd_english = True
    # 使用新的API设置活动对象
    armature = model.findArmature(bpy.context.active_object)
    if armature:
        bpy.context.view_layer.objects.active = armature
    else:
        print("No armature found.")
        return False
        
    mmd_english_test_bone_names = [
        'upper body', 'neck', 'head', 'shoulder_L', 'arm_L', 'elbow_L', 
        'wrist_L', 'leg_L', 'knee_L', 'ankle_L', 'shoulder_R', 'arm_R', 
        'elbow_R', 'wrist_R', 'leg_R', 'knee_R', 'ankle_R'
    ]
    
    missing_bones = [b for b in mmd_english_test_bone_names if b not in armature.data.bones]
    
    if missing_bones:
        print(f"Missing mmd_english test bone names: {missing_bones}")
        print("\nThis armature appears not to be an mmd_english armature")
        return False
        
    return True


def correct_root_center():
    print('\n')
    if not test_is_mmd_english_armature():
        print("This operator only works on armatures with mmd_english bone names.")
        return
        
    armature = bpy.context.active_object
    bpy.context.view_layer.objects.active = armature
    
    # 处理root骨骼
    bpy.ops.object.mode_set(mode='EDIT')
    arm_data = armature.data
    
    if "root" not in arm_data.edit_bones:
        root_bone = arm_data.edit_bones.new('root')
        root_bone.head = (0, 0, 0)
        root_bone.tail = (0, 0, 1)
        
        if "center" in arm_data.edit_bones:
            arm_data.edit_bones["center"].parent = root_bone
            arm_data.edit_bones["center"].use_connect = False
            
        print("Added MMD root bone.")
    
    # 重命名center骨骼和顶点组
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh_objects = model.find_MMD_MeshesList(armature)
    
    for o in mesh_objects:
        if "center" in o.vertex_groups and "center" in arm_data.bones:
            arm_data.bones["center"].name = "lower body"
            print("Renamed center bone to lower body bone.")
            
            bpy.ops.object.mode_set(mode='EDIT')
            if "leg_L" in arm_data.edit_bones and "leg_R" in arm_data.edit_bones:
                leg_l_head_z = arm_data.edit_bones["leg_L"].head.z
                leg_r_head_z = arm_data.edit_bones["leg_R"].head.z
                arm_data.edit_bones["lower body"].tail.z = 0.5 * (leg_l_head_z + leg_r_head_z)
            bpy.ops.object.mode_set(mode='OBJECT')
    
    # 处理center骨骼
    bpy.ops.object.mode_set(mode='EDIT')
    if "center" not in arm_data.edit_bones:
        center_bone = arm_data.edit_bones.new("center")
        print("Added center bone.")
        
        # 计算center骨骼位置
        if all(b in arm_data.edit_bones for b in ["knee_L", "knee_R", "leg_L", "leg_R"]):
            knee_l = arm_data.edit_bones["knee_L"].head
            knee_r = arm_data.edit_bones["knee_R"].head
            leg_l = arm_data.edit_bones["leg_L"].head
            leg_r = arm_data.edit_bones["leg_R"].head
            
            center_bone.head = 0.25 * (knee_l + knee_r + leg_l + leg_r)
            center_bone.tail = center_bone.head.copy()
            center_bone.tail.z -= 1
            
            if "root" in arm_data.edit_bones:
                center_bone.parent = arm_data.edit_bones["root"]
            
            if "lower body" in arm_data.edit_bones:
                arm_data.edit_bones["lower body"].parent = center_bone
            
            if "upper body" in arm_data.edit_bones:
                arm_data.edit_bones["upper body"].parent = center_bone
    
    bpy.ops.object.mode_set(mode='OBJECT')


def main(context):
    if context.scene.selected_miscellaneous_tools == "combine_2_bones":
        armature = model.findArmature(context.active_object)
        if armature:
            context.view_layer.objects.active = armature
            parent_bone_name, child_bone_name = analyze_selected_parent_child_bone_pair()
            if parent_bone_name and child_bone_name:
                combine_2_vg_1_vg(parent_bone_name, child_bone_name)
                combine_2_bones_1_bone(parent_bone_name, child_bone_name)
    
    elif context.scene.selected_miscellaneous_tools == "delete_unused":
        armature = model.findArmature(context.active_object)
        if armature:
            context.view_layer.objects.active = armature
            delete_unused_bones()
            delete_unused_vertex_groups()
    
    elif context.scene.selected_miscellaneous_tools == "mmd_ambient_white":
        all_materials_mmd_ambient_white()
    
    elif context.scene.selected_miscellaneous_tools == "correct_root_center":
        armature = model.findArmature(context.active_object)
        if armature:
            context.view_layer.objects.active = armature
            correct_root_center()


class MiscellaneousTools(bpy.types.Operator):
    """Miscellaneous Tools"""
    bl_idname = "mmd_tools_helper.miscellaneous_tools"
    bl_label = "Miscellaneous Tools"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


# 在注册类外定义属性，避免Blender 3.6的警告
bpy.types.Scene.selected_miscellaneous_tools = bpy.props.EnumProperty(
    items=[
        ('none', 'None', 'None'),
        ("combine_2_bones", "Combine 2 bones", 
         "Combine a parent-child pair of bones and their vertex groups to 1 bone and 1 vertex group"),
        ("delete_unused", "Delete unused bones and vertex groups", 
         "Delete all bones and vertex groups which have the word 'unused' in them"),
        ("mmd_ambient_white", "Set MMD ambient color to white", 
         "Change the MMD ambient color of all materials to white"),
        ("correct_root_center", "Correct MMD Root and Center bones", 
         "Correct MMD root and center bones")
    ],
    name="Select Function:",
    default='none'
)


def register():
    bpy.utils.register_class(MiscellaneousToolsPanel)
    bpy.utils.register_class(MiscellaneousTools)


def unregister():
    bpy.utils.unregister_class(MiscellaneousToolsPanel)
    bpy.utils.unregister_class(MiscellaneousTools)
    # 清理属性
    del bpy.types.Scene.selected_miscellaneous_tools


if __name__ == "__main__":
    register()
#register()