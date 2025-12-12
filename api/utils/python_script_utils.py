from typing import Optional, List, Dict, Any
import inspect
import ast
class PythonScriptUtils:
    @staticmethod    
    def _execute_python_script(script: str, params: Dict[str, Any]) -> Any:
        """执行Python脚本（通过AST解析+参数完全匹配定位用户自定义函数）"""
        try:
            # 步骤1：解析脚本AST，提取所有def定义的用户函数名称
            user_func_names = PythonScriptUtils._extract_user_functions_from_ast(script)
            if not user_func_names:
                raise Exception("未在脚本中找到def定义的用户函数")
            
            # 步骤2：执行脚本，获取全局环境
            globals_env = {
                '__builtins__': __builtins__,
                'inspect': inspect
            }
            exec(script, globals_env)
            
            # 步骤3：筛选参数与params完全匹配的函数
            target_functions = PythonScriptUtils._filter_functions_by_params(
                globals_env=globals_env,
                func_names=user_func_names,
                target_params=params
            )
            if not target_functions:
                param_keys = list(params.keys())
                raise Exception(f"未找到参数与 {param_keys} 完全匹配的用户函数")
            
            # 步骤4：尝试调用目标函数（默认取第一个匹配的函数）
            name, obj = target_functions[0]
            try:
                # 获取函数参数的类型注解
                sig = inspect.signature(obj)
                # 根据类型注解转换参数类型
                converted_params = PythonScriptUtils._convert_params_by_type_annotations(sig, params)
                # 使用转换后的参数调用函数
                result = obj(**converted_params)
            except Exception as e:
                raise Exception(f"函数 {name} 调用失败: {str(e)}")
            
            return result
            
        except Exception as e:
            raise Exception(f"脚本执行错误: {str(e)}")
    
    @staticmethod 
    def _convert_params_by_type_annotations(signature: inspect.Signature, params: Dict[str, Any]) -> Dict[str, Any]:
        """根据函数参数的类型注解转换参数类型
        
        Args:
            signature: 函数签名对象
            params: 原始参数字典
            
        Returns:
            Dict[str, Any]: 转换类型后的参数字典
        """
        converted_params = {}
        
        for param_name, param in signature.parameters.items():
            # 检查参数是否存在且有类型注解
            if param_name in params and param.annotation != inspect.Parameter.empty:
                param_value = params[param_name]
                # 如果参数值已经是目标类型，则不需要转换
                if isinstance(param_value, param.annotation):
                    converted_params[param_name] = param_value
                    continue
                
                # 尝试根据类型注解进行转换
                try:
                    # 处理常见类型的转换
                    if param.annotation == int:
                        # 尝试将字符串或浮点数转换为整数
                        converted_params[param_name] = int(param_value)
                    elif param.annotation == float:
                        # 尝试将字符串或整数转换为浮点数
                        converted_params[param_name] = float(param_value)
                    elif param.annotation == bool:
                        # 处理布尔值转换，支持字符串"true"/"false"或数字等
                        if isinstance(param_value, str):
                            converted_params[param_name] = param_value.lower() in ('true', 'yes', '1', 't', 'y')
                        else:
                            converted_params[param_name] = bool(param_value)
                    elif param.annotation == str:
                        # 转换为字符串
                        converted_params[param_name] = str(param_value)
                    # 可以根据需要添加更多类型转换逻辑
                    else:
                        # 对于其他类型，尝试直接转换
                        converted_params[param_name] = param.annotation(param_value)
                except (ValueError, TypeError):
                    # 如果转换失败，保留原始值
                    converted_params[param_name] = param_value
            else:
                # 如果参数没有类型注解或不存在于params中，保留原始值（如果存在）
                if param_name in params:
                    converted_params[param_name] = params[param_name]
        
        return converted_params

    @staticmethod 
    def _extract_user_functions_from_ast(script: str) -> List[str]:
        """通过AST解析提取脚本中所有def定义的函数名称"""
        tree = ast.parse(script)
        func_names = []
        for node in ast.walk(tree):
            # 识别函数定义节点（def）
            if isinstance(node, ast.FunctionDef):
                func_names.append(node.name)
            # 可选：识别异步函数定义节点（async def）
            elif isinstance(node, ast.AsyncFunctionDef):
                func_names.append(node.name)
        return func_names

    @staticmethod 
    def _filter_functions_by_params(globals_env: Dict[str, Any], func_names: List[str], target_params: Dict[str, Any]) -> List[tuple]:
        """筛选参数名称和数量与target_params完全匹配的函数"""
        target_param_keys = set(target_params.keys())
        matched_functions = []
        
        for func_name in func_names:
            obj = globals_env.get(func_name)
            if not obj or not callable(obj):
                continue
            
            # 解析函数参数签名
            try:
                sig = inspect.signature(obj)
                func_param_keys = set(sig.parameters.keys())
                
                # 筛选条件：函数参数与目标参数完全一致（数量和名称都匹配）
                if func_param_keys == target_param_keys:
                    matched_functions.append((func_name, obj))
            except ValueError:
                # 忽略无法解析签名的对象（如内置函数）
                continue
        
        return matched_functions
    