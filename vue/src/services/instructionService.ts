// 指令API服务
// 封装指令相关的API调用

import { httpClient } from './httpClient';
import {
  ApiResponse,
  Instruction,
  InstructionCategory,
  InstructionExecutionResult,
  InstructionApiService,
} from '@/types';

/**
 * 指令API服务类
 */
export class InstructionService implements InstructionApiService {
  private readonly basePath = '/instructions';

  /**
   * 获取指令分类列表（包含指令数据）
   * 一次性获取分类和指令，避免重复调用API
   */
  async getInstructionCategoriesWithInstructions(): Promise<ApiResponse<InstructionCategory[]>> {
    try {
      // 调用统一的指令接口
      const response = await httpClient.get<any>(`${this.basePath}`);
      
      if (response.data && response.data.categories) {
        // 转换API数据格式为前端使用格式
        const categories: InstructionCategory[] = response.data.categories.map((apiCategory: any) => {
          // 转换分类下的指令
          const instructions: Instruction[] = (apiCategory.items || []).map((apiInstruction: any) => ({
            id: apiInstruction.id,
            name: apiInstruction.name,
            description: apiInstruction.description,
            category: apiCategory.id,
            icon: apiInstruction.icon || 'default-icon',
            params: apiInstruction.params && Array.isArray(apiInstruction.params) && apiInstruction.params.length > 0 
              ? apiInstruction.params 
              : this.extractParamsFromScript(apiInstruction.python_script || ''),
            inputPorts: 1,
            outputPorts: 1,
            sort_order: apiInstruction.sort_order || 1,
            is_active: apiInstruction.is_active !== undefined ? apiInstruction.is_active : true,
            python_script: apiInstruction.python_script || ''
          }));
          
          return {
            id: apiCategory.id,
            name: apiCategory.name,
            description: apiCategory.description,
            expanded: true,
            instructions: instructions
          };
        });
        
        return {
          ...response,
          data: categories
        };
      }
      
      return response;
    } catch (error) {
      console.error('获取指令分类和指令失败:', error);
      throw error;
    }
  }

  /**
   * 获取指令分类列表
   * @deprecated 建议使用 getInstructionCategoriesWithInstructions 方法
   */
  async getInstructionCategories(): Promise<ApiResponse<InstructionCategory[]>> {
    try {
      // 调用统一的指令接口
      const response = await httpClient.get<any>(`${this.basePath}`);
      
      if (response.data && response.data.categories) {
        // 转换API数据格式为前端使用格式
        const categories: InstructionCategory[] = response.data.categories.map((apiCategory: any) => ({
          id: apiCategory.id,
          name: apiCategory.name,
          description: apiCategory.description,
          expanded: true,
          instructions: [] // 稍后填充
        }));
        
        return {
          ...response,
          data: categories
        };
      }
      
      return response;
    } catch (error) {
      console.error('获取指令分类失败:', error);
      throw error;
    }
  }

  /**
   * 获取指令列表
   */
  async getInstructions(categoryId?: string): Promise<ApiResponse<Instruction[]>> {
    try {
      // 调用统一的指令接口
      const response = await httpClient.get<any>(`${this.basePath}`);
      
      if (response.data && response.data.categories) {
        // 从分类中提取指令
        let allInstructions: any[] = [];
        
        response.data.categories.forEach((category: any) => {
          if (category.items) {
            const categoryInstructions = category.items.map((item: any) => ({
              ...item,
              category_id: category.id
            }));
            allInstructions = allInstructions.concat(categoryInstructions);
          }
        });
        
        // 如果指定了分类ID，则过滤指令
        if (categoryId) {
          allInstructions = allInstructions.filter(
            instruction => instruction.category_id === categoryId
          );
        }
        
        // 转换API数据格式为前端使用格式
        const instructions: Instruction[] = allInstructions.map(apiInstruction => ({
          id: apiInstruction.id,
          name: apiInstruction.name,
          description: apiInstruction.description,
          category: apiInstruction.category_id,
          icon: apiInstruction.icon || 'default-icon',
          params: apiInstruction.params && Array.isArray(apiInstruction.params) && apiInstruction.params.length > 0 
            ? apiInstruction.params 
            : this.extractParamsFromScript(apiInstruction.python_script || ''),
          inputPorts: 1,
          outputPorts: 1,
          sort_order: apiInstruction.sort_order || 1,
          is_active: apiInstruction.is_active !== undefined ? apiInstruction.is_active : true,
          python_script: apiInstruction.python_script || ''
        }));
        
        return {
          ...response,
          data: instructions
        };
      }
      
      return { ...response, data: [] };
    } catch (error) {
      console.error('获取指令列表失败:', error);
      throw error;
    }
  }

  /**
   * 从Python脚本中提取参数
   * 解析Python脚本中的execute函数定义、文档字符串和注释来提取参数信息
   */
  private extractParamsFromScript(script: string): any[] {
    if (!script || typeof script !== 'string') {
      return [];
    }

    const params: any[] = [];
    
    try {
      // 提取execute函数定义部分
      const executeFunctionMatch = script.match(/def\s+execute\s*\(\s*params\s*:\s*dict\s*\)/);
      if (!executeFunctionMatch) {
        // 如果没有显式的类型注解，尝试匹配更简单的函数定义
        const simpleExecuteMatch = script.match(/def\s+execute\s*\(\s*params\s*\)/);
        if (!simpleExecuteMatch) {
          return [];
        }
      }

      // 提取文档字符串或注释中的参数说明
      const docstringMatch = script.match(/"""[\s\S]*?"""|'''[\s\S]*?'''/);
      if (docstringMatch) {
        const docstring = docstringMatch[0];
        
        // 匹配参数说明行，如: "param_name: 描述信息"
        const paramPattern = /\s*(\w+):\s*(.+?)(?=\n\s*(?:\w+:|$))/g;
        let match;
        while ((match = paramPattern.exec(docstring)) !== null) {
          params.push({
            name: match[1],
            label: match[1].charAt(0).toUpperCase() + match[1].slice(1), // 首字母大写作为标签
            description: match[2].trim(),
            type: 'string', // 默认类型为字符串
            required: false,
            defaultValue: '',
            validation: {}
          });
        }
      }
      
      // 如果文档字符串中没有参数说明，尝试从代码中解析params的使用
      if (params.length === 0) {
        // 匹配params['param_name']或params["param_name"]的使用
        const paramUsagePattern = /params\s*\[\s*['"](\w+)['"]\s*\]/g;
        const paramNames = new Set<string>();
        let match;
        while ((match = paramUsagePattern.exec(script)) !== null) {
          paramNames.add(match[1]);
        }
        
        // 将唯一的参数名转换为参数对象
        paramNames.forEach(paramName => {
          params.push({
            name: paramName,
            label: paramName.charAt(0).toUpperCase() + paramName.slice(1),
            description: '',
            type: 'string',
            required: false,
            defaultValue: '',
            validation: {}
          });
        });
      }
    } catch (error) {
      console.error('提取脚本参数时出错:', error);
    }

    return params;
  }

  // 删除getInstructionType方法，不再进行类型判断

  /**
   * 获取单个指令详情
   * @deprecated 指令详情已在 /api/instructions 接口中返回，无需单独调用
   * 建议直接从已加载的指令列表中查找指令详情
   */
  async getInstruction(id: string): Promise<ApiResponse<Instruction>> {
    // 不再调用单独的API，而是从已加载的指令列表中查找
    try {
      const response = await this.getInstructionCategoriesWithInstructions();
      if (response.success && response.data) {
        // 从所有分类中查找指定ID的指令
        for (const category of response.data) {
          const instruction = category.instructions.find(inst => inst.id === id);
          if (instruction) {
            return {
              success: true,
              data: instruction
            };
          }
        }
      }
      
      throw new Error(`未找到ID为 ${id} 的指令`);
    } catch (error) {
      console.error(`获取指令详情失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 执行指令
   */
  async executeInstruction(
    instructionId: string,
    params: Record<string, any>,
    intputTypes?: { t: string[]; e: string[] }
  ): Promise<ApiResponse<InstructionExecutionResult>> {
    try {
      const requestData = {
        instruction_id: instructionId,
        script_params: params,
        input_types: intputTypes || { t: [], e: [] }
      };
      
      // 修复API路径，应该直接调用/instruction/execute而不是/instructions/execute
      return await httpClient.post<InstructionExecutionResult>(
        '/instruction/execute',
        requestData
      );
    } catch (error) {
      console.error(`执行指令失败 (ID: ${instructionId}):`, error);
      throw error;
    }
  }

  /**
   * 批量执行指令流程
   */
  async executeInstructionFlow(
    dataSourceId: string,
    instructions: Array<{
      instructionId: string;
      params: Record<string, any>;
    }>
  ): Promise<ApiResponse<InstructionExecutionResult[]>> {
    try {
      const requestData = {
        data_source_id: dataSourceId,
        instructions: instructions.map(inst => ({
          instruction_id: inst.instructionId,
          params: inst.params,
        })),
      };
      
      return await httpClient.post<InstructionExecutionResult[]>(
        `${this.basePath}/execute-flow`,
        requestData
      );
    } catch (error) {
      console.error('执行指令流程失败:', error);
      throw error;
    }
  }

  /**
   * 验证指令参数
   */
  async validateInstructionParams(
    instructionId: string,
    params: Record<string, any>
  ): Promise<ApiResponse<{ valid: boolean; errors?: string[] }>> {
    try {
      const requestData = {
        instruction_id: instructionId,
        params,
      };
      
      return await httpClient.post<{ valid: boolean; errors?: string[] }>(
        `${this.basePath}/validate-params`,
        requestData
      );
    } catch (error) {
      console.error(`验证指令参数失败 (ID: ${instructionId}):`, error);
      throw error;
    }
  }

  /**
   * 获取指令执行历史
   */
  async getInstructionHistory(
    instructionId?: string,
    limit: number = 50
  ): Promise<ApiResponse<InstructionExecutionResult[]>> {
    try {
      const params = {
        limit,
        ...(instructionId && { instruction_id: instructionId }),
      };
      
      return await httpClient.get<InstructionExecutionResult[]>(
        `${this.basePath}/history`,
        params
      );
    } catch (error) {
      console.error('获取指令执行历史失败:', error);
      throw error;
    }
  }

  /**
   * 安装依赖包
   */
  async installDependencies(dependencies?: string): Promise<ApiResponse<boolean>> {
    try {
      return await httpClient.post<boolean>(
        `/instruction/install-dependencies`,
        { dependencies } // 传递依赖包参数
      );
    } catch (error) {
      console.error('安装依赖包失败:', error);
      throw error;
    }
  }

  /**
   * 创建新指令
   */
  async createInstruction(data: any): Promise<ApiResponse<Instruction>> {
    try {
      return await httpClient.post<Instruction>(
        `/instruction/item/create`,
        data
      );
    } catch (error) {
      console.error('创建指令失败:', error);
      throw error;
    }
  }

  /**
   * 更新指令
   */
  async updateInstruction(id: string, _data: any): Promise<ApiResponse<Instruction>> {
    try {
      return await httpClient.put<Instruction>(
        `/instruction/item/${id}`,
        _data
      );
    } catch (error) {
      console.error(`更新指令失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 删除指令
   */
  async deleteInstruction(id: string): Promise<ApiResponse<boolean>> {
    try {
      return await httpClient.delete<boolean>(
        `/instruction/item/${id}`
      );
    } catch (error) {
      console.error(`删除指令失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 创建指令分类
   */
  async createCategory(_data: any): Promise<ApiResponse<InstructionCategory>> {
    try {
      return await httpClient.post<InstructionCategory>(
        `/instruction/category/create`,
        _data
      );
    } catch (error) {
      console.error('创建指令分类失败:', error);
      throw error;
    }
  }

  /**
   * 更新指令分类
   */
  async updateCategory(id: string, _data: any): Promise<ApiResponse<InstructionCategory>> {
    try {
      return await httpClient.put<InstructionCategory>(
        `/instruction/category/${id}`,
        _data
      );
    } catch (error) {
      console.error(`更新指令分类失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 删除指令分类
   */
  async deleteCategory(id: string): Promise<ApiResponse<boolean>> {
    try {
      return await httpClient.delete<boolean>(
        `/instruction/category/${id}`
      );
    } catch (error) {
      console.error(`删除指令分类失败 (ID: ${id}):`, error);
      throw error;
    }
  }

  /**
   * 批量操作指令
   */
  async batchOperateInstructions(
    _operation: 'enable' | 'disable' | 'delete',
    _ids: string[]
  ): Promise<ApiResponse<boolean>> {
    try {
      return await httpClient.post<boolean>(
        `/instruction/batch`,
        {
          operation: _operation,
          ids: _ids
        }
      );
    } catch (error) {
      console.error('批量操作指令失败:', error);
      throw error;
    }
  }

  /**
   * 排序指令
   */
  async sortInstructions(_sortedIds: string[]): Promise<ApiResponse<boolean>> {
    try {
      return await httpClient.post<boolean>(
        `/instruction/sort`,
        {
          sortedIds: _sortedIds
        }
      );
    } catch (error) {
      console.error('排序指令失败:', error);
      throw error;
    }
  }
}

// 创建指令服务实例
export const instructionService = new InstructionService();