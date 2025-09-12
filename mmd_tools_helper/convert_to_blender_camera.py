import bpy

class MMDCameraToBlenderCameraPanel(bpy.types.Panel):
    """Convert MMD cameras back to Blender cameras"""
    bl_idname = "OBJECT_PT_mmd_camera_to_blender_camera"
    bl_label = "Convert MMD Cameras to Blender cameras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+使用UI替代TOOLS
    bl_category = "mmd_tools_helper"  # 在侧边栏中的分类

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row = layout.row()
        row.operator("mmd_tools_helper.mmd_camera_to_blender_camera", 
                    text="Convert MMD cameras to Blender cameras")
        row = layout.row()

def main(context):
    # 遍历场景中的所有相机
    cameras = [o for o in bpy.context.scene.objects if o.type == 'CAMERA']
    
    for camera in cameras:
        # 解锁相机的所有变换
        camera.lock_location = (False, False, False)
        camera.lock_rotation = (False, False, False)
        camera.lock_scale = (False, False, False)

        # 禁用所有驱动
        if camera.animation_data is not None:
            for d in camera.animation_data.drivers:
                d.mute = True

        # 处理相机父对象（如果是MMD相机控制器）
        if camera.parent is not None and hasattr(camera.parent, "mmd_type"):
            if camera.parent.mmd_type == 'CAMERA':
                # Blender 2.8+中使用collection API替代scene.objects.unlink
                if camera.parent.users_collection:
                    coll = camera.parent.users_collection[0]
                    coll.objects.unlink(camera.parent)
                # 清除父关系但保留变换
                bpy.context.view_layer.objects.active = camera
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

class MMDCameraToBlenderCamera(bpy.types.Operator):
    """Convert MMD cameras back to Blender cameras"""
    bl_idname = "mmd_tools_helper.mmd_camera_to_blender_camera"
    bl_label = "Convert MMD Cameras to Blender cameras"
    bl_options = {'REGISTER', 'UNDO'}  # 添加撤销支持

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "MMD cameras converted to Blender cameras")  # 操作反馈
        return {'FINISHED'}


def register():
    # 修正类名拼写错误（原代码少了一个M）
    bpy.utils.register_class(MMDCameraToBlenderCamera)
    bpy.utils.register_class(MMDCameraToBlenderCameraPanel)


def unregister():
    bpy.utils.unregister_class(MMDCameraToBlenderCamera)
    bpy.utils.unregister_class(MMDCameraToBlenderCameraPanel)


if __name__ == "__main__":
    register()
