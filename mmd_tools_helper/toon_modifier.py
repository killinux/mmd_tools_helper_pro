import bpy
from . import model  # 确保包含 model.find_MMD_MeshesList 函数

class MMDToonModifierPanel(bpy.types.Panel):
    """用于修改 MMD 卡通材质渲染效果的面板"""
    bl_idname = "OBJECT_PT_mmd_toon_modifier"
    bl_label = "MMD Toon Modifier"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+ 使用 UI 区域（侧边栏）
    bl_category = "mmd_tools_helper"  # 侧边栏分类标签
    bl_context = "objectmode"  # 仅在物体模式显示

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 面板标题
        row = layout.row()
        row.label(text="MMD Toon Modifier", icon="MATERIAL")
        
        # 混合模式选择
        layout.prop(scene, "ToonModifierBlendType", text="Blend Type")
        
        # 颜色选择器
        layout.prop(scene, "ToonModifierColor", text="Color")
        
        # 应用按钮
        row = layout.row()
        row.operator("mmd_tools_helper.toon_modifier", text="Apply Toon Modification")


def main(context):
    # 获取当前视图层（Blender 2.8+ 新特性）
    view_layer = context.view_layer
    active_obj = view_layer.objects.active
    
    # 查找所有 MMD 网格对象
    mesh_objects_list = model.find_MMD_MeshesList(active_obj)
    if not mesh_objects_list:
        raise Exception("未找到关联的 MMD 模型，请确保选中 MMD 模型对象")
    
    # 遍历所有网格对象修改材质
    for obj in mesh_objects_list:
        # 跳过非网格对象
        if obj.type != 'MESH':
            continue
            
        # 激活当前对象（用于材质操作）
        view_layer.objects.active = obj
        
        # 遍历对象的所有材质
        for material in obj.data.materials:
            # 跳过未使用节点的材质
            if not material.use_nodes:
                continue
                
            # 查找标记为 "toon_modifier" 的节点
            for node in material.node_tree.nodes:
                if node.label == "toon_modifier":
                    # 更新颜色属性
                    if 'Color2' in node.inputs:
                        node.inputs['Color2'].default_value[0] = context.scene.ToonModifierColor[0]
                        node.inputs['Color2'].default_value[1] = context.scene.ToonModifierColor[1]
                        node.inputs['Color2'].default_value[2] = context.scene.ToonModifierColor[2]
                        # 保持 Alpha 通道不变
                        node.inputs['Color2'].default_value[3] = 1.0
                    
                    # 更新混合模式
                    node.blend_type = context.scene.ToonModifierBlendType


class MMDToonModifier(bpy.types.Operator):
    """修改 MMD 卡通材质的渲染效果"""
    bl_idname = "mmd_tools_helper.toon_modifier"
    bl_label = "Modify MMD Toon"
    bl_options = {"REGISTER", "UNDO"}  # 支持撤销操作


# 在注册时定义场景属性（避免重复定义）
def register_properties():
    # 卡通修改器颜色属性
    bpy.types.Scene.ToonModifierColor = bpy.props.FloatVectorProperty(
        name="Toon Color",
        description="调整卡通材质的颜色",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    # 混合模式枚举属性
    bpy.types.Scene.ToonModifierBlendType = bpy.props.EnumProperty(
        items=[
            ('MIX', 'Mix', '混合模式'),
            ('ADD', 'Add', '叠加模式'),
            ('MULTIPLY', 'Multiply', '相乘模式'),
            ('SUBTRACT', 'Subtract', '减法模式'),
            ('SCREEN', 'Screen', '屏幕模式'),
            ('DIVIDE', 'Divide', '除法模式'),
            ('DIFFERENCE', 'Difference', '差值模式'),
            ('DARKEN', 'Darken', '变暗模式'),
            ('LIGHTEN', 'Lighten', '变亮模式'),
            ('OVERLAY', 'Overlay', '覆盖模式'),
            ('DODGE', 'Dodge', '减淡模式'),
            ('BURN', 'Burn', '加深模式'),
            ('HUE', 'Hue', '色相模式'),
            ('SATURATION', 'Saturation', '饱和度模式'),
            ('VALUE', 'Value', '明度模式'),
            ('COLOR', 'Color', '颜色模式'),
            ('SOFT_LIGHT', 'Soft Light', '柔光模式'),
            ('LINEAR_LIGHT', 'Linear Light', '线性光模式')
        ],
        name="Blend Type",
        description="选择卡通材质的混合模式",
        default='MULTIPLY'
    )


def unregister_properties():
    # 注销场景属性
    del bpy.types.Scene.ToonModifierColor
    del bpy.types.Scene.ToonModifierBlendType


def register():
    register_properties()
    bpy.utils.register_class(MMDToonModifierPanel)
    bpy.utils.register_class(MMDToonModifier)
    print("MMD Toon Modifier 插件已注册")


def unregister():
    bpy.utils.unregister_class(MMDToonModifier)
    bpy.utils.unregister_class(MMDToonModifierPanel)
    unregister_properties()
    print("MMD Toon Modifier 插件已注销")


if __name__ == "__main__":
    register()
