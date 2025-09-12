bl_info = {
    "name": "MMD Background Color Picker",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > mmd_tools_helper",
    "description": "Sets world background color with contrasting text color",
    "category": "MMD Tools",
}

import bpy

class MMDBackgroundColorPicker_Panel(bpy.types.Panel):
    """Selects world background color and a contrasting text color"""
    bl_idname = "OBJECT_PT_mmd_background_color_picker"
    bl_label = "MMD Background Color Picker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"

    def draw(self, context):
        layout = self.layout
        
        # 添加颜色属性控件
        layout.prop(context.scene, "mmd_background_color")
        
        # 添加操作按钮
        layout.operator("mmd_tools_helper.background_color_picker", 
                      text="Apply Background Color")


class MMDBackgroundColorPicker(bpy.types.Operator):
    """Sets world background color and contrasting text color"""
    bl_idname = "mmd_tools_helper.background_color_picker"
    bl_label = "Apply MMD Background Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 确保世界环境存在
        if not context.scene.world:
            context.scene.world = bpy.data.worlds.new("World")
        
        # 确保世界环境使用节点
        if not context.scene.world.use_nodes:
            context.scene.world.use_nodes = True
        
        # 获取背景节点并设置颜色
        nodes = context.scene.world.node_tree.nodes
        background_node = nodes.get("Background")
        if background_node:
            # Blender 3.6 中背景颜色是第一个输入
            bg_color = context.scene.mmd_background_color
            background_node.inputs[0].default_value = (bg_color[0], bg_color[1], bg_color[2], 1.0)
        
        # 计算对比文本颜色
        bg_r, bg_g, bg_b = context.scene.mmd_background_color
        text_r = 1.0 - bg_r
        text_g = 1.0 - bg_g
        text_b = 1.0 - bg_b
        
        # 设置3D视图文本颜色
        context.preferences.themes[0].view_3d.text = (text_r, text_g, text_b, 1.0)
        context.preferences.themes[0].view_3d.text_hi = (text_r, text_g, text_b, 1.0)
        
        self.report({'INFO'}, "Background color updated successfully")
        return {'FINISHED'}


def register():
    # 在注册时定义属性（Blender 3.x 推荐方式）
    bpy.types.Scene.mmd_background_color = bpy.props.FloatVectorProperty(
        name="Background Color",
        description="Set world background color",
        default=(0.1, 0.1, 0.1),  # 深色默认值更符合MMD风格
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    bpy.utils.register_class(MMDBackgroundColorPicker_Panel)
    bpy.utils.register_class(MMDBackgroundColorPicker)


def unregister():
    bpy.utils.unregister_class(MMDBackgroundColorPicker_Panel)
    bpy.utils.unregister_class(MMDBackgroundColorPicker)
    
    # 安全删除属性
    if hasattr(bpy.types.Scene, "mmd_background_color"):
        del bpy.types.Scene.mmd_background_color


if __name__ == "__main__":
    register()
