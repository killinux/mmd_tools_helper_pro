import bpy

# 定义场景属性（移至全局，便于正确注册和注销）
bpy.types.Scene.BackgroundColor = bpy.props.FloatVectorProperty(
    name="Background Color",
    description="Set world background color",
    default=(1.0, 1.0, 1.0),
    min=0.0,
    max=1.0,
    subtype='COLOR',
    size=3
)

class MMDBackgroundColorPicker_Panel(bpy.types.Panel):
    """Selects world background color and a contrasting text color"""
    bl_idname = "OBJECT_PT_mmd_background_color_picker"
    bl_label = "MMD background color picker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 适配Blender 2.8+的UI区域
    bl_category = "mmd_tools_helper"  # 侧边栏分类

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row = layout.row()
        layout.prop(context.scene, "BackgroundColor")
        row.operator("mmd_tools_helper.background_color_picker", 
                    text="MMD background color picker")
        row = layout.row()


def main(context):
    # 处理3D视图的世界显示设置
    for screen in bpy.data.screens:
        try:  # 添加错误处理，避免特定屏幕不存在时出错
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.show_world = True
        except Exception as e:
            print(f"处理屏幕 {screen.name} 时出错: {e}")

    # 设置世界背景颜色
    if context.scene.world is None:
        # 如果没有世界环境，创建一个
        context.scene.world = bpy.data.worlds.new("World")
    context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
        context.scene.BackgroundColor[0],
        context.scene.BackgroundColor[1],
        context.scene.BackgroundColor[2],
        1.0  # Alpha通道
    )

    # 计算对比文本颜色（确保可读性）
    bg_r, bg_g, bg_b = context.scene.BackgroundColor
    text_r = 1.0 - bg_r
    text_g = 1.0 - bg_g
    text_b = 1.0 - bg_b

    # 设置3D视图文本颜色（适配Blender 2.8+的API）
    context.preferences.themes[0].view_3d.text_hi = (text_r, text_g, text_b, 1.0)


class MMDBackgroundColorPicker(bpy.types.Operator):
    """Selects world background color and a contrasting text color"""
    bl_idname = "mmd_tools_helper.background_color_picker"
    bl_label = "MMD background color picker"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "Background color updated successfully")  # 操作反馈
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MMDBackgroundColorPicker)
    bpy.utils.register_class(MMDBackgroundColorPicker_Panel)


def unregister():
    bpy.utils.unregister_class(MMDBackgroundColorPicker)
    bpy.utils.unregister_class(MMDBackgroundColorPicker_Panel)
    # 清理场景属性
    del bpy.types.Scene.BackgroundColor


if __name__ == "__main__":
    register()
