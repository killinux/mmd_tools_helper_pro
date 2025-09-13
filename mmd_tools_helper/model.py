import bpy

print("model.py---")

def findRoot(obj):
    """查找 MMD 模型的根对象（ROOT 类型）"""
    if obj is not None:
        if hasattr(obj, "mmd_type") and obj.mmd_type == 'ROOT':
            return obj
        else:
            return findRoot(obj.parent)
    else:
        return None

def armature(root):
    """从根对象的子对象中查找骨架（ARMATURE）"""
    armatures = []
    if root is None:
        return None
    for c in root.children:
        if c.type == 'ARMATURE':
            # 移除 hide_viewport 修改，避免上下文错误
            armatures.append(c)
    if len(armatures) == 1:
        return armatures[0]
    if len(armatures) == 0:
        print("警告：未找到骨架对象")
        return None
    if len(armatures) > 1:
        print(f"错误：找到多个骨架对象 {armatures}")
        return None

def __allObjects(obj):
    """递归获取对象的所有子对象（内部辅助函数）"""
    r = []
    for child in obj.children:
        r.append(child)
        r += __allObjects(child)
    return r

def allObjects(obj, root):
    """获取从指定对象（或根对象）开始的所有对象"""
    if obj is None:
        obj = root
    return [obj] + __allObjects(obj)

def meshes(root):
    """从根对象中筛选出 MMD 网格（MESH 类型且 mmd_type 为 NONE）"""
    arm = armature(root)
    if arm is None:
        return []
    else:
        return [
            x for x in allObjects(arm, root) 
            if x.type == 'MESH' and hasattr(x, "mmd_type") and x.mmd_type == 'NONE'
        ]

def find_MMD_Armature(obj):
    """查找 MMD 模型的骨架（通过根对象）"""
    root = findRoot(obj)
    if root is None:
        print('未选中任何 MMD 模型')
    else:
        return armature(root)

def findArmature(obj):
    """从任意对象查找关联的骨架（支持多种对象类型）"""
    # 若对象本身是骨架，直接返回
    if obj.type == 'ARMATURE':
        return obj  # 移除 hide_viewport 修改
    # 若父对象是骨架，返回父对象
    if obj.parent is not None and obj.parent.type == 'ARMATURE':
        return obj.parent  # 移除 hide_viewport 修改
    # 若对象是 MMD 根节点，从根节点查找骨架
    if hasattr(obj, "mmd_type") and obj.mmd_type == 'ROOT':
        return armature(obj)
    # 若对象是空物体，尝试从空物体查找骨架
    if obj.type == 'EMPTY':
        return armature(obj)
    # 未找到骨架
    print(f"警告：未从对象 {obj.name} 找到关联的骨架")
    return None

def find_MMD_MeshesList(obj):
    """查找 MMD 模型的所有网格（通过根对象）"""
    root = findRoot(obj)
    if root is None:
        print('未选中任何 MMD 模型')
    else:
        return list(meshes(root))

def findMeshesList(obj):
    """从任意对象查找关联的网格列表"""
    mesheslist = []
    # 若对象是骨架，收集其所有子网格
    if obj.type == 'ARMATURE':
        for child in obj.children:
            if child.type == 'MESH':
                mesheslist.append(child)
        return mesheslist
    # 若对象是网格，查找其父骨架的所有子网格
    if obj.type == 'MESH':
        if obj.parent is not None and obj.parent.type == 'ARMATURE':
            for child in obj.parent.children:
                if child.type == 'MESH':
                    mesheslist.append(child)
            return mesheslist
        # 若网格无父骨架，仅返回自身
        return [obj]
    # 若对象是 MMD 根节点，从根节点查找网格
    if hasattr(obj, "mmd_type") and obj.mmd_type == 'ROOT':
        return list(meshes(obj))
    # 若对象是空物体，从空物体查找网格
    if obj.type == 'EMPTY':
        return list(meshes(obj))
    # 未找到网格
    return mesheslist

def find_mmd_rigid_bodies_list(root):
    """查找 MMD 模型的刚体列表（从 root 的子对象 "rigidbodies" 中）"""
    if root is None:
        print("错误：根对象为空，无法查找刚体")
        return []
    # 查找名为 "rigidbodies" 的空对象
    rigidbodies_empty = None
    for child in root.children:
        if child.type == 'EMPTY' and child.name == "rigidbodies":
            rigidbodies_empty = child
            break
    if rigidbodies_empty is None:
        print("警告：未找到名为 'rigidbodies' 的空对象")
        return []
    # 返回刚体空对象的所有子对象
    return list(rigidbodies_empty.children)

def find_mmd_joints_list(root):
    """查找 MMD 模型的关节列表（从 root 的子对象 "joints" 中）"""
    if root is None:
        print("错误：根对象为空，无法查找关节")
        return []
    # 查找名为 "joints" 的空对象
    joints_empty = None
    for child in root.children:
        if child.type == 'EMPTY' and child.name == "joints":
            joints_empty = child
            break
    if joints_empty is None:
        print("警告：未找到名为 'joints' 的空对象")
        return []
    # 返回关节空对象的所有子对象
    return list(joints_empty.children)

def test():
    """测试函数：验证各功能是否正常工作"""
    print("test---from model.py")
    if not hasattr(bpy.context, "active_object") or bpy.context.active_object is None:
        print("未选中任何对象，测试终止")
        return
    
    active_obj = bpy.context.active_object
    print(f"活跃对象类型：{active_obj.type}")
    
    # 测试根对象查找
    root = findRoot(active_obj)
    print(f"根对象：{root.name if root else 'None'}")
    
    # 测试 MMD 网格列表查找
    mmd_meshes = find_MMD_MeshesList(active_obj)
    print(f"MMD 网格列表：{[m.name for m in mmd_meshes]}")
    
    # 测试 MMD 骨架查找
    mmd_armature = find_MMD_Armature(active_obj)
    print(f"MMD 骨架：{mmd_armature.name if mmd_armature else 'None'}\n")
    
    # 测试通用网格列表查找
    meshes = findMeshesList(active_obj)
    print(f"通用网格列表：{[m.name for m in meshes]}")
    
    # 测试通用骨架查找
    armature = findArmature(active_obj)
    print(f"通用骨架：{armature.name if armature else 'None'}\n")
    
    # 测试刚体和关节查找（仅当根对象存在时）
    if root:
        rigid_bodies = find_mmd_rigid_bodies_list(root)
        print(f"刚体列表：{[rb.name for rb in rigid_bodies]}")
        
        joints = find_mmd_joints_list(root)
        print(f"关节列表：{[j.name for j in joints]}\n")
    else:
        print("根对象不存在，跳过刚体和关节测试")

# 取消注释可运行测试
# test()
