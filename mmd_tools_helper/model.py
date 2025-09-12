import bpy
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# 核心：确保属性注册（关键修复）
# --------------------------
def register_scene_properties():
    # 仅在属性未注册时才注册，避免重复注册错误
    if not hasattr(bpy.types.Scene, "selected_armature_to_diagnose"):
        bpy.types.Scene.selected_armature_to_diagnose = bpy.props.PointerProperty(
            name="待诊断骨骼",
            type=bpy.types.Object,
            poll=lambda self, obj: obj and obj.type == 'ARMATURE',  # 确保obj不为空
            description="选择要诊断的MMD骨骼对象"
        )

def unregister_scene_properties():
    if hasattr(bpy.types.Scene, "selected_armature_to_diagnose"):
        del bpy.types.Scene.selected_armature_to_diagnose

# --------------------------
# 模型工具函数（纯读取，无任何修改）
# --------------------------
def findRoot(obj):
    """查找根对象（仅读取）"""
    if not obj:
        return None
    current = obj
    while current.parent:
        current = current.parent
        if hasattr(current, 'mmd_type') and current.mmd_type == 'ROOT':
            return current
    # 检查自身是否为根
    if hasattr(obj, 'mmd_type') and obj.mmd_type == 'ROOT':
        return obj
    return None

def findArmature(obj):
    """查找骨骼对象（纯读取，不修改任何属性）"""
    if not obj:
        return None
    
    # 情况1：自身就是骨骼
    if obj.type == 'ARMATURE':
        return obj
    
    # 情况2：父对象是骨骼
    if obj.parent and obj.parent.type == 'ARMATURE':
        return obj.parent
    
    # 情况3：从根对象的子级中查找
    root = findRoot(obj)
    if root:
        for child in root.children:  # 遍历子级（纯读取，无修改）
            if child.type == 'ARMATURE':
                return child
    
    # 情况4：从空对象的子级中查找
    if obj.type == 'EMPTY':
        for child in obj.children:  # 遍历子级（纯读取，无修改）
            if child.type == 'ARMATURE':
                return child
    
    return None

def get_all_bones(armature_obj):
    """获取所有骨骼名称（纯读取）"""
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return []
    return [bone.name for bone in armature_obj.data.bones]

# --------------------------
# 骨骼诊断逻辑
# --------------------------
class MMD_Armature_Diagnoser:
    BASE_MMD_BONES = [
        "センター", "上半身", "下半身", "頭", "首",
        "左肩", "左腕", "左手", "左指",
        "右肩", "右腕", "右手", "右指",
        "左足", "左足首", "左足先",
        "右足", "右足首", "右足先"
    ]
    
    @classmethod
    def diagnose(cls, armature_obj):
        if not armature_obj or armature_obj.type != 'ARMATURE':
            return {"error": "无效的骨骼对象"}
        
        current_bones = get_all_bones(armature_obj)
        return {
            "armature_name": armature_obj.name,
            "total_bones": len(current_bones),
            "missing_basic_bones": [b for b in cls.BASE_MMD_BONES if b not in current_bones],
            "ik_bones": [b.name for b in armature_obj.data.bones if b.ik_constraint],
            "has_ik": any(b.ik_constraint for b in armature_obj.data.bones),
            "warning": ["骨骼数量异常少，可能不完整"] if len(current_bones) < 10 else []
        }
    
    @classmethod
    def print_diagnosis(cls, result):
        if "error" in result:
            logger.error(result["error"])
            return
        
        print("\n===== MMD骨骼诊断结果 =====")
        print(f"骨骼对象: {result['armature_name']}")
        print(f"总骨骼数量: {result['total_bones']}")
        
        if result["missing_basic_bones"]:
            print(f"\n缺失基础骨骼 ({len(result['missing_basic_bones'])}):")
            for bone in result["missing_basic_bones"]:
                print(f"  - {bone}")
        else:
            print("\n✓ 所有基础骨骼都存在")
            
        print(f"\nIK骨骼数量: {len(result['ik_bones'])}")
        if result["ik_bones"]:
            print("IK骨骼列表:")
            for bone in result["ik_bones"]:
                print(f"  - {bone}")
                
        if result["warning"]:
            print("\n警告:")
            for warn in result["warning"]:
                print(f"  - {warn}")
        print("\n===========================")

# --------------------------
# UI面板（纯绘制，不修改数据）
# --------------------------
class MMD_PT_Armature_Diagnose_Panel(bpy.types.Panel):
    bl_idname = "MMD_PT_armature_diagnose"
    bl_label = "MMD骨骼诊断工具"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MMD工具'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 检查属性是否存在（容错处理）
        if not hasattr(scene, "selected_armature_to_diagnose"):
            layout.label(text="属性未注册，请重新启用插件", icon='ERROR')
            return
        
        box = layout.box()
        box.label(text="骨骼选择", icon='ARMATURE_DATA')
        box.prop(scene, "selected_armature_to_diagnose")
        
        box = layout.box()
        box.label(text="诊断操作", icon='TOOL_SETTINGS')
        box.operator("mmd.diagnose_armature", text="执行诊断", icon='CHECKMARK')
        
        if "diagnosis_result" in scene:
            box = layout.box()
            box.label(text="诊断状态", icon='INFO')
            box.label(text=f"最后诊断: {scene['diagnosis_result'].get('armature_name', '无')}")

# --------------------------
# 操作符（唯一允许修改数据的上下文）
# --------------------------
class MMD_OT_Diagnose_Armature(bpy.types.Operator):
    bl_idname = "mmd.diagnose_armature"
    bl_label = "诊断骨骼"
    bl_description = "诊断选中的MMD骨骼结构"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # 检查属性是否存在
        if not hasattr(scene, "selected_armature_to_diagnose"):
            self.report({'ERROR'}, "属性未注册，请重新安装插件")
            return {'CANCELLED'}
        
        target_armature = scene.selected_armature_to_diagnose
        if not target_armature or target_armature.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择有效的骨骼对象")
            return {'CANCELLED'}
        
        # 尝试显示骨骼（仅在此处执行修改操作）
        try:
            target_armature.hide_viewport = False
        except AttributeError:
            self.report({'WARNING'}, "无法修改骨骼可见性，但诊断将继续")
        
        # 执行诊断
        result = MMD_Armature_Diagnoser.diagnose(target_armature)
        MMD_Armature_Diagnoser.print_diagnosis(result)
        scene["diagnosis_result"] = result
        
        self.report({'INFO'}, f"诊断完成: {target_armature.name}")
        return {'FINISHED'}

# --------------------------
# 插件注册/注销（确保属性优先注册）
# --------------------------
classes = (MMD_PT_Armature_Diagnose_Panel, MMD_OT_Diagnose_Armature)

def register():
    # 1. 优先注册属性
    register_scene_properties()
    # 2. 注册UI和操作符
    for cls in classes:
        bpy.utils.register_class(cls)
    logger.info("插件注册完成")

def unregister():
    # 1. 注销UI和操作符
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # 2. 最后注销属性
    unregister_scene_properties()
    logger.info("插件注销完成")

if __name__ == "__main__":
    register()
    