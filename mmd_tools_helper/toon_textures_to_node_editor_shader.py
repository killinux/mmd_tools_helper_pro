import bpy
from . import model

# ------------------------------
# 1. 卡通纹理转颜色梯度工具函数
# ------------------------------
def toon_image_to_color_ramp(toon_color_ramp_node, toon_image):
    """从卡通纹理图像提取颜色信息并配置ColorRamp节点"""
    if not toon_image or not toon_image.pixels:
        raise Warning("卡通纹理图像无效或为空")

    # 提取像素数据（每4个值为一个RGBA像素）
    pixel_list = []
    for i in range(0, len(toon_image.pixels), 4):
        rgba = toon_image.pixels[i:i+4]
        pixel_list.append(rgba)

    # 采样32个梯度点（平衡精度与性能）
    sample_count = 32
    step = max(1, len(pixel_list) // sample_count)
    gradient_samples = [pixel_list[i] for i in range(0, len(pixel_list), step)]
    
    # 确保至少有2个采样点（ColorRamp需要首尾）
    if len(gradient_samples) < 2:
        gradient_samples = [pixel_list[0], pixel_list[-1]]

    # 清除现有中间控制点（保留首尾）
    while len(toon_color_ramp_node.color_ramp.elements) > 2:
        toon_color_ramp_node.color_ramp.elements.remove(
            toon_color_ramp_node.color_ramp.elements[1]
        )

    # 设置首尾颜色
    toon_color_ramp_node.color_ramp.elements[0].color = gradient_samples[0]
    toon_color_ramp_node.color_ramp.elements[-1].color = gradient_samples[-1]

    # 添加中间控制点
    for i in range(1, len(gradient_samples) - 1):
        position = i / (len(gradient_samples) - 1)  # 0~1范围
        element = toon_color_ramp_node.color_ramp.elements.new(position)
        element.color = gradient_samples[i]
        # 非阴影区域Alpha设为0（卡通渲染常规处理）
        if i > len(gradient_samples) // 2:
            element.color[3] = 0.0

# ------------------------------
# 2. 材质节点清理工具函数
# ------------------------------
def clear_material_nodes(material):
    """清理材质节点树，仅保留材质输出节点"""
    if not material.node_tree:
        material.use_nodes = True  # 确保节点树存在

    # 查找现有输出节点，若无则创建
    output_node = next(
        (n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'),
        None
    )
    if not output_node:
        output_node = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (1450, 800)

    # 删除所有非输出节点
    for node in list(material.node_tree.nodes):
        if node != output_node:
            material.node_tree.nodes.remove(node)

    return output_node

# ------------------------------
# 3. 面板类（Blender 3.6侧边栏）
# ------------------------------
class MMDToonTexturesToNodeEditorShaderPanel(bpy.types.Panel):
    """MMD卡通纹理节点编辑器面板"""
    bl_idname = "OBJECT_PT_mmd_toon_render_node_editor"
    bl_label = "MMD Toon Nodes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # 侧边栏显示（按N键打开）
    bl_category = "mmd_tools_helper"
    bl_order = 7  # 面板显示顺序

    def draw(self, context):
        layout = self.layout
        layout.label(text="卡通渲染节点生成", icon="MATERIAL")
        layout.operator(
            "mmd_tools_helper.mmd_toon_render_node_editor",
            text="创建MMD卡通节点"
        )

# ------------------------------
# 4. 节点创建核心函数
# ------------------------------
def create_toon_nodes(material, lamp_obj):
    """为指定材质创建完整的MMD卡通渲染节点树"""
    # 清理现有节点并获取输出节点
    output_node = clear_material_nodes(material)
    links = material.node_tree.links

    # ------------------------------
    # 创建基础节点
    # ------------------------------
    # 主材质节点（PBR标准节点）
    principled_bsdf = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled_bsdf.location = (-800, 800)
    principled_bsdf.inputs['Base Color'].default_value = (
        material.diffuse_color[0],
        material.diffuse_color[1],
        material.diffuse_color[2],
        1.0
    )

    # 灯光数据节点
    light_data = material.node_tree.nodes.new('ShaderNodeLightData')
    light_data.light_object = lamp_obj
    light_data.location = (-530, -50)

    # 向量点积节点（计算法线与灯光夹角）
    vector_dot = material.node_tree.nodes.new('ShaderNodeVectorMath')
    vector_dot.operation = 'DOT_PRODUCT'
    vector_dot.location = (-520, 470)

    # 数学运算节点（调整范围）
    math_add = material.node_tree.nodes.new('ShaderNodeMath')
    math_add.operation = 'ADD'
    math_add.inputs[1].default_value = 1.0
    math_add.location = (-325, 470)

    math_mul1 = material.node_tree.nodes.new('ShaderNodeMath')
    math_mul1.operation = 'MULTIPLY'
    math_mul1.inputs[1].default_value = 0.5
    math_mul1.location = (-90, 470)

    math_mul2 = material.node_tree.nodes.new('ShaderNodeMath')
    math_mul2.operation = 'MULTIPLY'
    math_mul2.location = (120, 470)

    # 卡通颜色梯度节点
    toon_ramp = material.node_tree.nodes.new('ShaderNodeValToRGB')
    toon_ramp.location = (340, 470)
    toon_ramp.color_ramp.interpolation = 'CONSTANT'  # 硬边缘卡通效果

    # 混合节点（纹理叠加）
    mix_toon = material.node_tree.nodes.new('ShaderNodeMixRGB')
    mix_toon.blend_type = 'MULTIPLY'
    mix_toon.inputs[0].default_value = 1.0
    mix_toon.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
    mix_toon.location = (690, 470)
    mix_toon.label = "卡通叠加"

    mix_final = material.node_tree.nodes.new('ShaderNodeMixRGB')
    mix_final.blend_type = 'MULTIPLY'
    mix_final.inputs[0].default_value = 1.0
    mix_final.location = (1000, 470)

    mix_sphere = material.node_tree.nodes.new('ShaderNodeMixRGB')
    mix_sphere.blend_type = 'ADD'
    mix_sphere.inputs[0].default_value = 1.0
    mix_sphere.location = (1240, 470)

    # 几何节点（获取UV和法线）
    geo_uv = material.node_tree.nodes.new('ShaderNodeGeometry')
    geo_uv.location = (620, 250)

    geo_normal = material.node_tree.nodes.new('ShaderNodeGeometry')
    geo_normal.location = (620, -50)

    # 纹理节点
    tex_diffuse = material.node_tree.nodes.new('ShaderNodeTexImage')
    tex_diffuse.location = (820, 250)
    tex_diffuse.label = "漫反射纹理"

    tex_sphere = material.node_tree.nodes.new('ShaderNodeTexImage')
    tex_sphere.location = (820, -50)
    tex_sphere.label = "球面纹理"

    # ------------------------------
    # 连接节点
    # ------------------------------
    # 灯光与法线计算链路
    links.new(vector_dot.inputs[0], principled_bsdf.outputs['Normal'])
    links.new(vector_dot.inputs[1], light_data.outputs['Light Vector'])
    links.new(math_add.inputs[0], vector_dot.outputs['Value'])
    links.new(math_mul1.inputs[0], math_add.outputs['Value'])
    links.new(math_mul2.inputs[0], math_mul1.outputs['Value'])

    # 阴影处理链路
    links.new(math_mul2.inputs[1], light_data.outputs['Shadow'])

    # 卡通纹理链路
    links.new(toon_ramp.inputs['Fac'], math_mul2.outputs['Value'])
    links.new(mix_toon.inputs['Color1'], toon_ramp.outputs['Color'])
    links.new(mix_toon.inputs['Fac'], toon_ramp.outputs['Alpha'])

    # 漫反射纹理链路
    links.new(tex_diffuse.inputs['Vector'], geo_uv.outputs['UV'])
    links.new(mix_final.inputs['Color1'], mix_toon.outputs['Color'])
    links.new(mix_final.inputs['Color2'], tex_diffuse.outputs['Color'])

    # 球面纹理链路
    links.new(tex_sphere.inputs['Vector'], geo_normal.outputs['Normal'])
    links.new(mix_sphere.inputs['Color1'], mix_final.outputs['Color'])
    links.new(mix_sphere.inputs['Color2'], tex_sphere.outputs['Color'])

    # 最终输出链路
    links.new(output_node.inputs['Surface'], mix_sphere.outputs['Color'])
    links.new(output_node.inputs['Alpha'], principled_bsdf.outputs['Alpha'])

    # ------------------------------
    # 加载材质现有纹理（MMD标准纹理槽）
    # ------------------------------
    if hasattr(material, 'texture_slots'):
        for slot_idx, slot in enumerate(material.texture_slots):
            if not slot or not slot.texture or slot.texture.type != 'IMAGE':
                continue
            
            tex_image = slot.texture.image
            if not tex_image:
                continue

            # 槽0：漫反射纹理
            if slot_idx == 0:
                tex_diffuse.image = tex_image
            # 槽1：卡通纹理
            elif slot_idx == 1:
                toon_image_to_color_ramp(toon_ramp, tex_image)
            # 槽2：球面纹理
            elif slot_idx == 2:
                tex_sphere.image = tex_image
                if hasattr(slot, 'blend_type'):
                    mix_sphere.blend_type = slot.blend_type

    # 处理无漫反射纹理的情况
    if not tex_diffuse.image:
        # 移除原连接，改用基础色
        if mix_final.inputs['Color2'].links:
            links.remove(mix_final.inputs['Color2'].links[0])
        links.new(mix_final.inputs['Color2'], principled_bsdf.outputs['Base Color'])

# ------------------------------
# 5. 主执行函数
# ------------------------------
def main(context):
    # 获取MMD模型的网格对象
    mesh_objects = model.findMeshesList(context.active_object)
    if not mesh_objects:
        raise Exception("未找到MMD模型的网格对象，请先选择MMD模型")

    # 确保存在太阳灯（卡通渲染基础光源）
    lamp_obj = None
    # 查找现有太阳灯
    for obj in context.scene.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN':
            lamp_obj = obj
            break
    # 若无则创建
    if not lamp_obj:
        light_data = bpy.data.lights.new("MMD_Toon_Light", 'SUN')
        lamp_obj = bpy.data.objects.new("MMD_Toon_Light", light_data)
        context.scene.collection.objects.link(lamp_obj)
        lamp_obj.rotation_euler = (1.106, 0, 0.785)  # 优化角度

    # 为每个网格的每个材质创建节点
    for mesh in mesh_objects:
        if mesh.type != 'MESH':
            continue
        context.view_layer.objects.active = mesh
        
        for material in mesh.data.materials:
            create_toon_nodes(material, lamp_obj)

# ------------------------------
# 6. 操作符类
# ------------------------------
class MMDToonTexturesToNodeEditorShader(bpy.types.Operator):
    """创建MMD卡通渲染节点树"""
    bl_idname = "mmd_tools_helper.mmd_toon_render_node_editor"
    bl_label = "创建MMD卡通节点"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销
    bl_description = "为MMD模型生成卡通渲染节点树"

    @classmethod
    def poll(cls, context):
        """仅当选中有效对象时启用按钮"""
        return context.active_object is not None

    def execute(self, context):
        try:
            main(context)
            self.report({'INFO'}, "卡通节点创建成功！")
            return {'FINISHED'}
        except Warning as w:
            self.report({'WARNING'}, str(w))
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

# ------------------------------
# 7. 注册/注销
# ------------------------------
def register():
    bpy.utils.register_class(MMDToonTexturesToNodeEditorShaderPanel)
    bpy.utils.register_class(MMDToonTexturesToNodeEditorShader)

def unregister():
    bpy.utils.unregister_class(MMDToonTexturesToNodeEditorShaderPanel)
    bpy.utils.unregister_class(MMDToonTexturesToNodeEditorShader)

if __name__ == "__main__":
    register()
