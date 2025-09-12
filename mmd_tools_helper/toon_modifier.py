import bpy
from . import model

# ------------------------------
# 场景属性注册与注销（符合Blender 3.x规范）
# ------------------------------
def register_scene_properties():
    """注册卡通修改器所需的场景属性"""
    # 卡通修改器颜色属性
    bpy.types.Scene.ToonModifierColor = bpy.props.FloatVectorProperty(
        name="Toon Modifier Color",
        description="Color to modify toon rendering",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    # 卡通修改器混合模式属性
    bpy.types.Scene.ToonModifierBlendType = bpy.props.EnumProperty(
        items=[
            ('MIX', 'Mix', 'Mix blend mode'),
            ('ADD', 'Add', 'Add blend mode'),
            ('MULTIPLY', 'Multiply', 'Multiply blend mode'),
            ('SUBTRACT', 'Subtract', 'Subtract blend mode'),
            ('SCREEN', 'Screen', 'Screen blend mode'),
            ('DIVIDE', 'Divide', 'Divide blend mode'),
            ('DIFFERENCE', 'Difference', 'Difference blend mode'),
            ('DARKEN', 'Darken', 'Darken blend mode'),
            ('LIGHTEN', 'Lighten', 'Lighten blend mode'),
            ('OVERLAY', 'Overlay', 'Overlay blend mode'),
            ('DODGE', 'Dodge', 'Dodge blend mode'),
            ('BURN', 'Burn', 'Burn blend mode'),
            ('HUE', 'Hue', 'Hue blend mode'),
            ('SATURATION', 'Saturation', 'Saturation blend mode'),
            ('VALUE', 'Value', 'Value blend mode'),
            ('COLOR', 'Color', 'Color blend mode'),
            ('SOFT_LIGHT', 'Soft Light', 'Soft Light blend mode'),
            ('LINEAR_LIGHT', 'Linear Light', 'Linear Light blend mode')
        ],
        name="Blend Type",
        description="Blend mode for toon modification",
        default='MULTIPLY'
    )

def unregister_scene_properties():
    """注销场景属性，防止插件卸载后残留"""
    if hasattr(bpy.types.Scene, "ToonModifierColor"):
        del bpy.types.Scene.ToonModifierColor
    if hasattr(bpy.types.Scene, "ToonModifierBlendType"):
        del bpy.types.Scene.ToonModifierBlendType

# ------------------------------
# 面板类（适配Blender 3.6侧边栏）
# ------------------------------
class MMDToonModifierPanel(bpy.types.Panel):
    """User can modify the rendering of toon texture color"""
    bl_idname = "OBJECT_PT_mmd_toon_modifier"
    bl_label = "MMD Toon Modifier"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 关键：替换废弃的TOOLS为UI（侧边栏显示）
    bl_category = "mmd_tools_helper"
    bl_order = 8  # 面板显示顺序（在卡通节点面板之后）

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 面板标题
        layout.label(text="Adjust Toon Appearance", icon="MATERIAL")
        
        # 混合模式选择
        layout.prop(scene, "ToonModifierBlendType", text="Blend Mode")
        
        # 颜色选择器
        layout.prop(scene, "ToonModifierColor", text="Tint Color")
        
        # 应用按钮
        layout.operator(
            "mmd_tools_helper.toon_modifier",
            text="Apply Toon Modifications"
        )

# ------------------------------
# 主功能实现
# ------------------------------
def main(context):
    """应用卡通效果修改：更新混合模式和颜色"""
    # 获取MMD模型的网格对象列表
    mesh_objects = model.findMeshesList(context.active_object)
    if not mesh_objects:
        raise Exception("No MMD meshes found. Please select an MMD model first.")
    
    # 获取场景设置的参数
    blend_type = context.scene.ToonModifierBlendType
    color = context.scene.ToonModifierColor
    
    # 遍历所有网格对象的材质
    for obj in mesh_objects:
        if obj.type != 'MESH':
            continue
            
        # 激活当前对象（避免上下文错误）
        context.view_layer.objects.active = obj
        
        # 处理每个材质
        for material in obj.data.materials:
            if not material.node_tree:
                continue  # 跳过无节点树的材质
            
            # 查找标记为"toon_modifier"的混合节点
            for node in material.node_tree.nodes:
                if node.label == "toon_modifier" and node.type == 'MIX_RGB':
                    # 更新混合模式
                    node.blend_type = blend_type
                    # 更新颜色（保留原有Alpha值）
                    node.inputs['Color2'].default_value = (
                        color[0],
                        color[1],
                        color[2],
                        node.inputs['Color2'].default_value[3]  # 保持原有Alpha
                    )

# ------------------------------
# 操作符类（执行修改操作）
# ------------------------------
class MMDToonModifier(bpy.types.Operator):
    """Modify the rendering of toon texture color"""
    bl_idname = "mmd_tools_helper.toon_modifier"
    bl_label = "Apply Toon Modifications"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作
    bl_description = "Update toon shading with selected blend mode and color"

    @classmethod
    def poll(cls, context):
        """按钮启用条件：有活跃对象且能找到MMD网格"""
        return (context.active_object is not None 
                and model.findMeshesList(context.active_object) is not None)

    def execute(self, context):
        try:
            main(context)
            self.report({'INFO'}, "Toon modifications applied successfully!")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# ------------------------------
# 注册与注销函数
# ------------------------------
def register():
    register_scene_properties()
    bpy.utils.register_class(MMDToonModifierPanel)
    bpy.utils.register_class(MMDToonModifier)

def unregister():
    bpy.utils.unregister_class(MMDToonModifierPanel)
    bpy.utils.unregister_class(MMDToonModifier)
    unregister_scene_properties()

if __name__ == "__main__":
    register()
