import bpy
print("mmd_lamp_setup.py-->")
class MMDLampSetupPanel(bpy.types.Panel):
    """One-click Lamp Setup for mmd_tools"""
    bl_idname = "OBJECT_PT_mmd_lamp_setup"
    bl_label = "MMD Lamp Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 改为UI区域，适配Blender 2.8+
    bl_category = "mmd_tools_helper"  # 在N面板中的分类

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row.label(text="MMD Lamp", icon="LIGHT_SUN")  # 图标名称更新
        row = layout.row()
        row.operator("mmd_tools_helper.mmd_lamp_setup", text="MMD Lamp")
        row = layout.row()
        row = layout.row()

def lamp_setup(o):
    o.rotation_mode = 'XYZ'
    o.rotation_euler[0] = 0.785398  # 45度（弧度）
    o.rotation_euler[1] = 0
    o.rotation_euler[2] = 0.785398  # 45度（弧度）
    o.location = (30, -30, 30)
    o.scale = (2, 2, 2)

    # 灯光数据设置（适配Blender 2.8+ API）
    o.data.type = 'SUN'
    o.data.color = (0.6, 0.6, 0.6)
    o.data.shadow.cascade_count = 4  # 阴影采样更新
    o.data.shadow_soft_size = 2.0
    # 阴影颜色设置在Blender 3.6中通过世界环境节点管理

def main(context):
    # 移除游戏引擎相关设置（Blender 2.8+已移除内置游戏引擎）
    
    # 更新视图着色模式
    context.space_data.shading.type = 'MATERIAL'  # 替代TEXTURED
    
    # 环境光设置（使用节点系统，适配Blender 2.8+）
    world = context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        context.scene.world = world
    
    # 确保世界环境使用节点
    world.use_nodes = True
    tree = world.node_tree
    
    # 清除默认节点
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # 创建环境光节点
    bg_node = tree.nodes.new(type='ShaderNodeBackground')
    env_light_node = tree.nodes.new(type='ShaderNodeEnvironmentLight')
    output_node = tree.nodes.new(type='ShaderNodeOutputWorld')
    
    # 设置节点位置
    bg_node.location = (-300, 0)
    env_light_node.location = (0, 0)
    output_node.location = (300, 0)
    
    # 连接节点
    tree.links.new(bg_node.outputs["Background"], env_light_node.inputs["Surface"])
    tree.links.new(env_light_node.outputs["Light"], output_node.inputs["Surface"])
    
    # 设置环境光强度
    env_light_node.inputs["Strength"].default_value = 1.0
    
    # 颜色管理设置
    context.scene.display_settings.display_device = 'NONE'  # 改为大写
    
    # 查找或创建灯光
    lamp_objects = [ob for ob in context.scene.objects if ob.type == 'LIGHT']
    if not lamp_objects:
        # 创建新灯光（Blender 2.8+使用lights替代lamps）
        lamp_data = bpy.data.lights.new("MMD_Lamp", "SUN")
        lamp_object = bpy.data.objects.new("MMD_Lamp", lamp_data)
        # 将灯光添加到集合
        context.collection.objects.link(lamp_object)
        lamp_objects.append(lamp_object)
    
    # 保存当前活动对象
    active_object = context.active_object
    
    # 设置灯光参数
    o = lamp_objects[0]
    context.view_layer.objects.active = o  # 更新活动对象的方式
    lamp_setup(o)
    
    # 恢复之前的活动对象
    if active_object:
        context.view_layer.objects.active = active_object

class MMDLampSetup(bpy.types.Operator):
    """One-click Lamp Setup for mmd_tools"""
    bl_idname = "mmd_tools_helper.mmd_lamp_setup"
    bl_label = "MMD Lamp Setup"
    bl_options = {'REGISTER', 'UNDO'}  # 添加撤销支持

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "MMD Lamp setup completed")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MMDLampSetup)
    bpy.utils.register_class(MMDLampSetupPanel)

def unregister():
    bpy.utils.unregister_class(MMDLampSetup)
    bpy.utils.unregister_class(MMDLampSetupPanel)

if __name__ == "__main__":
    register()
  