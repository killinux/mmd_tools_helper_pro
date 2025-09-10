# Scales the Blender grid, thereby making it unnecessary to scale MMD models.

import bpy
import math
print("mmd_view.py--->>UI->->>")

class MMDViewPanel(bpy.types.Panel):
    """Camera and Grid to be same as MikuMikuDance"""
    bl_idname = "OBJECT_PT_mmd_view"
    bl_label = "MMD View"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"

    def draw(self, context):
        print("mmd_view.py--draw-->")
        layout = self.layout
        row = layout.row()

        row.label(text="MMD View", icon="CAMERA_DATA")
        row = layout.row()
        row.operator("mmd_tools_helper.mmd_view", text = "MMD View")
        row = layout.row()

def main(context):
    # 获取场景中的相机，如无则创建
    camera_objects = [ob for ob in bpy.context.scene.objects if ob.type == 'CAMERA']
    if not camera_objects:
        camera_data = bpy.data.cameras.new("Camera")
        camera_object = bpy.data.objects.new("Camera", camera_data)
        bpy.context.collection.objects.link(camera_object)
        bpy.context.scene.camera = camera_object

    # 保存当前活动对象
    active_object = bpy.context.active_object if bpy.context.active_object else bpy.context.scene.objects[-1]

    # 设置相机属性
    camera = bpy.context.scene.camera
    bpy.context.view_layer.objects.active = camera
    bpy.ops.mmd_tools.convert_to_mmd_camera(
        scale=1, 
        bake_animation=False, 
        camera_source='CURRENT', 
        min_distance=0.1
    )

    # 设置相机父对象（空物体）的位置和旋转
    camera.parent.location = (0, 0, 10)
    camera.parent.rotation_euler = (0, 0, 0)
    
    # 设置相机自身位置和旋转
    camera.location = (0, -45, 0)
    camera.rotation_euler = (math.pi/2, 0, 0)
    
    # 设置相机视角
    camera.parent.mmd_camera.angle = 0.523599

    # 更新所有3D视图的网格和视角设置
    for screen in ['Animation', 'Scripting', 'UV Editing', 'Default']:
        if screen in bpy.data.screens:
            for area in bpy.data.screens[screen].areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            # Blender 3.6 中网格相关属性移至 overlay 下
                            space.overlay.grid_lines = 20
                            space.overlay.grid_scale = 5  # 修复 grid_scale 属性位置
                            space.region_3d.view_perspective = 'CAMERA'
                            #space.show_world = True

    # 设置世界环境和主题
    if "Background" in bpy.context.scene.world.node_tree.nodes:
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    bpy.context.preferences.themes[0].view_3d.space.text_hi = (0, 0, 0)

    # 恢复之前的活动对象
    bpy.context.view_layer.objects.active = active_object

class MMDView(bpy.types.Operator):
    """Camera and Grid to be same as MikuMikuDance"""
    bl_idname = "mmd_tools_helper.mmd_view"
    bl_label = "MMD View"

    def execute(self, context):
        main(context)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MMDView)
    bpy.utils.register_class(MMDViewPanel)

def unregister():
    bpy.utils.unregister_class(MMDView)
    bpy.utils.unregister_class(MMDViewPanel)

if __name__ == "__main__":
    print("mmd_view.py---main--?????")
    register()
register()