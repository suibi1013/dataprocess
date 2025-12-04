<template>
  <Modal
    v-model:visible="localVisible"
    :title="isEdit ? '编辑指令' : '新增指令'"
    :ok-text="isEdit ? '保存' : '创建'"
    :cancel-text="'取消'"
    :loading="loading"
    :width="800"
    :close-on-click-modal="false"
    @ok="handleSave"
    @cancel="handleCancel"
  >
    <form @submit.prevent="handleSave">
      <!-- 基本信息 -->
      <div class="form-section">
        <h4>基本信息</h4>
        <div class="form-grid">
          <!-- 指令名称 -->
          <div class="form-item">
            <label class="form-label required">指令名称</label>
            <input 
              v-model="formData.name"
              type="text"
              class="form-input"
              placeholder="请输入指令名称"
              maxlength="50"
              @blur="validateName"
            >
            <div v-if="errors.name" class="error-message">{{ errors.name }}</div>
          </div>

          <!-- 指令分类 -->
          <div class="form-item">
            <label class="form-label required">指令分类</label>
            <select 
              v-model="formData.category"
              class="form-select"
              @change="validateCategory"
            >
              <option value="">请选择分类</option>
              <option 
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </option>
            </select>
            <div v-if="errors.category" class="error-message">{{ errors.category }}</div>
          </div>

          <!-- 指令图标 -->
          <div class="form-item">
            <label class="form-label">指令图标</label>
            <div class="icon-picker">
              <input 
                v-model="formData.icon"
                type="text" 
                class="form-input"
                placeholder="输入图标名称或选择"
                maxlength="20"
                disabled
              >
              <div class="icon-preview">
                <component v-if="formData.icon && formData.icon.startsWith('el-icon-')" :is="getIconComponent(formData.icon)"></component>
                <span v-else>{{ formData.icon || '?' }}</span>
              </div>
              <button 
                type="button" 
                class="icon-select-btn"
                @click="showIconSelector = true"
              >
                选择图标
              </button>
            </div>
          </div>

          <!-- 排序顺序 -->
          <div class="form-item">
            <label class="form-label">排序顺序</label>
            <input 
              v-model.number="formData.sort_order"
              type="number"
              class="form-input"
              placeholder="输入数字越小越靠前"
              min="1"
              max="999"
            >
            <div v-if="errors.sort_order" class="error-message">{{ errors.sort_order }}</div>
          </div>


        </div>

        <!-- 指令描述 -->
        <div class="form-item">
          <label class="form-label">指令描述</label>
          <textarea 
            v-model="formData.description"
            class="form-textarea"
            placeholder="请输入指令描述，简要说明指令的功能和用途（选填）"
            rows="3"
            maxlength="200"
            @blur="validateDescription"
          ></textarea>
          <div v-if="errors.description" class="error-message">{{ errors.description }}</div>
          <div class="char-count">{{ formData.description.length }}/200</div>
        </div>
      </div>

      <!-- 指令脚本 -->
      <div class="form-section">
        <h3>指令脚本</h3>
        <div class="form-item">
          <label class="form-label required">Python脚本</label>
          <div class="script-editor">
            <textarea 
              v-model="formData.python_script"
              class="script-textarea"
              placeholder="请输入Python脚本代码\n\n# 参数可通过params字典获取，如params['param_name']\n# 处理结果请返回，如return {'result': data}\n\ndef execute(params):\n    # 示例代码\n    return {'result': 'Hello World'}"
              rows="10"
              @blur="validateScript"
            ></textarea>
            <div class="script-helper">
              <div class="helper-title">使用说明</div>
              <ul>
                <li>脚本必须包含函数体</li>
                <li>参数名称需与指令配置的参数名称一致</li>
                <li>结果通过return返回给输出参数</li>
                <li>输出参数只能有一个</li>
              </ul>
            </div>
          </div>
          <div v-if="errors.python_script" class="error-message">{{ errors.python_script }}</div>
        </div>
      </div>

      <!-- 参数配置 -->
        <div class="form-section">
          <div class="section-header">
            <h3>参数配置</h3>
          </div>       
        
        <div class="params-container">
          <div 
            v-for="(param, index) in formData.params"
            :key="index"
            class="param-item"
            draggable="true"
            @dragstart="onDragStart($event, index)"
            @dragover.prevent="onDragOver($event, index)"
            @drop="onDrop($event, index)"
            @dragend="onDragEnd"
            :class="{ 'drag-over': dragOverIndex === index }"
          >
            <div class="param-header">
              <span class="param-index">参数 {{ index + 1 }}</span>
              <span class="drag-handle">☰</span>
              <button 
                class="btn btn-sm btn-danger delete-param-btn"
                @click="removeParameter(index)"
              >
                <i class="icon-trash"></i> 删除
              </button>
            </div>
            
            <div class="param-form-grid">
              <!-- 参数中文名称 -->
              <div class="form-item">
                <label class="form-label required">中文名称</label>
                <input 
                  v-model="param.label"
                  type="text"
                  class="form-input"
                  placeholder="请输入中文名称"
                  maxlength="20"
                  @blur="validateParamLabel(param.label, index)"
                >
                <div v-if="errors[`param_${index}_label`]" class="error-message">{{ errors[`param_${index}_label`] }}</div>
              </div>

              <!-- 参数属性名称 -->
              <div class="form-item">
                <label class="form-label required">属性名称</label>
                <input 
                  v-model="param.name"
                  type="text"
                  class="form-input"
                  placeholder="请输入属性名称（只能包含英文字母、数字和下划线）"
                  maxlength="20"
                  @input="param.name = param.name.replace(/[^a-zA-Z0-9_]/g, '')"
                  @blur="validateParamName(param.name, index)"
                >
                <div v-if="errors[`param_${index}_name`]" class="error-message">{{ errors[`param_${index}_name`] }}</div>
              </div>

              <!-- 参数类型 -->
              <div class="form-item">
                <label class="form-label required">参数类型</label>
                <select 
                  v-model="param.type"
                  class="form-select"
                  @change="onParamTypeChange(param, index)"
                >
                  <option value="string">字符串</option>
                  <option value="number">数字</option>
                  <option value="boolean">布尔值</option>
                  <option value="select">下拉单选</option>
                  <option value="select_excelpath">下拉单选-excel路径</option>
                  <option value="file">文件</option>
                </select>
              </div>



              <!-- 默认值 -->
              <div v-if="param.type !== 'checkbox'" class="form-item">
                <label class="form-label">默认值</label>
                <input 
                  v-model="param.defaultValue"
                  type="text"
                  class="form-input"
                  placeholder="请输入默认值"
                  maxlength="100"
                >
              </div>

              <!-- 是否必需 -->
              <div class="form-item checkbox-item">
                <div class="checkbox-wrapper">
                  <input 
                    v-model="param.required"
                    type="checkbox"
                    :id="`required_${index}`"
                  >
                  <label :for="`required_${index}`">是否必需</label>
                </div>
              </div>
            </div>

            <!-- 参数描述 -->
            <div class="form-item">
              <label class="form-label">参数描述</label>
              <textarea 
                v-model="param.description"
                class="form-textarea"
                placeholder="请输入参数描述"
                rows="2"
                maxlength="100"
              ></textarea>
              <div class="char-count">{{ param.description?.length || 0 }}/100</div>
            </div>
            
            <!-- 数据接口地址 -->
            <div class="form-item">
              <label class="form-label">数据接口地址</label>
              <input 
                v-model="param.apiUrl"
                type="text"
                class="form-input"
                placeholder="请输入数据接口地址（选填）"
                maxlength="200"
              >
            </div>

            <!-- 参数方向 -->
            <div class="form-item inline-radio">
              <label class="form-label required inline-label">参数方向</label>
              <div class="radio-group inline-options">
                <label class="radio-option">
                  <input 
                    type="radio" 
                    v-model.number="param.direction" 
                    :value="0" 
                  >
                  <span>输入参数</span>
                </label>
                <label class="radio-option">
                  <input 
                    type="radio" 
                    v-model.number="param.direction" 
                    :value="1" 
                  >
                  <span>输出参数</span>
                </label>
                <label class="radio-option">
                  <input 
                    type="radio" 
                    v-model.number="param.direction" 
                    :value="2" 
                  >
                  <span>回写参数</span>
                </label>
              </div>
            </div>

          </div>
          <!-- 添加参数按钮 -->
          <div class="add-param-button-container">
            <button 
              ref="addParamButton"
              class="btn btn-sm btn-primary"
              @click="addParameter"
              :disabled="formData.params.length >= 10"
            >
              <i class="icon-plus"></i> 添加参数
            </button>
          </div>
        </div>
      </div>
      </form>

      <!-- 图标选择器弹窗 -->
      <Modal
        v-model:visible="showIconSelector"
        title="选择图标"
        :ok-text="'确定'"
        :cancel-text="'取消'"
        :width="600"
        @ok="confirmIconSelection"
        @cancel="cancelIconSelection"
      >
        <div class="icon-selector-content">
          <div class="icon-search">
            <input 
              v-model="iconSearchKeyword"
              type="text"
              class="form-input"
              placeholder="搜索图标..."
            >
          </div>
          <div class="icon-list">
            <div 
              v-for="icon in filteredIcons"
              :key="icon"
              class="icon-item"
              :class="{ selected: selectedIcon === icon }"
              @click="selectedIcon = icon"
            >
              <!-- 转换图标类名为组件名 -->
              <component :is="getIconComponent(icon)"></component>
              <span>{{ icon }}</span>
            </div>
          </div>
        </div>
      </Modal>
    </Modal>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, computed, watch, onMounted } from 'vue';
import Modal from '@/components/Common/Modal.vue';
import type { Instruction } from '@/types/instruction';
import { instructionService } from '@/services/instructionService';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

interface FormData {
  name: string;
  description: string;
  category: string;
  icon?: string;
  params: Array<{
    name: string;
    type: string;
    label: string;
    required: boolean;
    description?: string;
    defaultValue?: any;
    direction?: number; // 0: 输入参数, 1: 输出参数，2: 回写参数
    validation?: {
      pattern?: string;
      message?: string;
    };
    multiple?: boolean;
    columns?: string[];
    apiUrl?: string;

  }>;
  sort_order?: number;
  python_script: string;
}

interface ErrorState {
  name?: string;
  description?: string;
  category?: string;
  python_script?: string;
  [key: string]: string | undefined;
}

export default defineComponent({
  name: 'AddInstructionModal',
  components: {
    Modal
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    instruction: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    // 使用本地状态来控制Modal显示，避免直接修改props
    const localVisible = ref(props.visible);
    const loading = ref(false);
    const categories = ref<any[]>([]);
    const errors = reactive<ErrorState>({});
    const iconSearchKeyword = ref('');
    const selectedIcon = ref('');
    const showIconSelector = ref(false);

    // 将图标组件名称转换为el-icon格式
    const commonIcons = Object.keys(ElementPlusIconsVue).map(key => {
      // Element Plus图标组件命名规则：Xxx -> el-icon-xxx
      return 'el-icon-' + key.replace(/([A-Z])/g, '-$1').toLowerCase().substring(1);
    });

    // 过滤后的图标列表
    const filteredIcons = computed(() => {
      if (!iconSearchKeyword.value.trim()) {
        return commonIcons;
      }
      return commonIcons.filter(icon => 
        icon.toLowerCase().includes(iconSearchKeyword.value.toLowerCase())
      );
    });
    
    // 同步外部visible变化到本地状态
    watch(() => props.visible, (newValue) => {
      localVisible.value = newValue;
    });
    
    // 当本地状态变化时通知父组件
    watch(localVisible, (newValue) => {
      if (!newValue) {
        emit('close');
      }
    });
    
    // 表单数据
    const formData = reactive<FormData>({
      name: '',
      description: '',
      category: '',
      icon: 'code',
      params: [],
      sort_order: 1,
      python_script: `def execute(params):
    # 请在这里编写指令的Python代码
    # 参数可以通过params字典获取，如params['param_name']
    # 处理结果请通过return返回
    return {'result': 'Hello World'}`
    });

    // 编辑状态标志
    const isEdit = ref(false);

    // 加载分类数据
    const loadCategories = async () => {
      try {
        const response = await instructionService.getInstructionCategoriesWithInstructions();
        if (response.success && response.data) {
          categories.value = response.data;
          // 如果有分类数据，且不是编辑模式，且没有选中的分类，则自动选择第一个分类
          if (categories.value.length > 0 && !isEdit.value && !formData.category) {
            formData.category = categories.value[0].id;
          }
        }
      } catch (error) {
        console.error('加载分类失败:', error);
      }
    };

    // 重置表单
    const resetForm = () => {
      formData.name = '';
      formData.description = '';
      formData.category = '';
      formData.icon = 'code';
      formData.params = [];
      formData.sort_order = 1;
      formData.python_script = `def execute(params):
    # 请在这里编写指令的Python代码
    # 参数可以通过params字典获取，如params['param_name']
    # 处理结果请通过return返回
    return {'result': 'Hello World'}`;
      
      // 清空错误信息
      Object.keys(errors).forEach(key => {
        delete errors[key];
      });
      
      // 重置后，如果有分类数据，且不是编辑模式，自动选择第一个分类
      if (categories.value.length > 0 && !isEdit.value) {
        formData.category = categories.value[0].id;
      }
    };

    // 填充表单数据
    const fillFormData = (instruction: any) => {
      resetForm();
      formData.name = instruction.name || '';
      formData.description = instruction.description || '';
      formData.category = instruction.category_id || instruction.category || '';
      formData.icon = instruction.icon || 'code';
      formData.sort_order = instruction.sort_order || 1;
      // 正确处理params字段，确保参数设置正确回写
      if (instruction.params && Array.isArray(instruction.params)) {
        // 深拷贝参数数组，避免引用问题
        formData.params = JSON.parse(JSON.stringify(instruction.params)).map((param: any) => {
          // 确保参数对象结构完整
          const cleanParam = {
            name: param.name || '',
            type: param.type || 'string',
            label: param.label || '',
            required: param.required || false,
            description: param.description || '',
            defaultValue: param.defaultValue !== undefined ? param.defaultValue : '',
            direction: param.direction !== undefined ? param.direction : 0, // 默认设置为输入参数
            apiUrl: param.apiUrl || ''
          };
          
          return cleanParam;
        });
      }
      
      // 设置Python脚本
      if (instruction.python_script) {
        formData.python_script = instruction.python_script;
      }
    };

    // 表单验证
    const validateForm = (): boolean => {
      let isValid = true;
      
      // 清空所有错误
      Object.keys(errors).forEach(key => {
        delete errors[key];
      });
      
      // 验证必填字段
      if (!formData.name.trim()) {
        errors.name = '请输入指令名称';
        isValid = false;
      }
      
      // 指令描述不再是必填项
      // if (!formData.description.trim()) {
      //   errors.description = '请输入指令描述';
      //   isValid = false;
      // }
      
      if (!formData.category) {
        errors.category = '请选择指令分类';
        isValid = false;
      }
      
      if (!formData.python_script.trim()) {
        errors.python_script = '请输入Python脚本';
        isValid = false;
      } else if (!/def\s+\w+\s*\(/.test(formData.python_script)) {
        errors.python_script = '脚本必须包含函数体';
        isValid = false;
      }
      
      // 验证排序顺序
      if (formData.sort_order !== undefined && formData.sort_order !== null && (formData.sort_order < 1 || formData.sort_order > 999 || !Number.isInteger(formData.sort_order))) {
        errors.sort_order = '排序顺序必须是1-999之间的整数';
        isValid = false;
      }
      
      // 验证参数
      formData.params.forEach((param, index) => {
        if (!param.name.trim()) {
          errors[`param_${index}_name`] = '请输入参数名称';
          isValid = false;
        }
         
        // 验证参数中文名称为必填
        if (!param.label.trim()) {
          errors[`param_${index}_label`] = '请输入参数中文名称';
          isValid = false;
        }         
      });
      
      return isValid;
    };

    // 单个字段验证
    const validateName = () => {
      if (!formData.name.trim()) {
        errors.name = '请输入指令名称';
      } else {
        delete errors.name;
      }
    };

    const validateDescription = () => {
      // 指令描述不再是必填项，移除验证逻辑
      delete errors.description;
    };

    const validateCategory = () => {
      if (!formData.category) {
        errors.category = '请选择指令分类';
      } else {
        delete errors.category;
      }
    };

    const validateScript = () => {
      if (!formData.python_script.trim()) {
        errors.python_script = '请输入Python脚本';
      } else if (!/def\s+\w+\s*\(/.test(formData.python_script)) {
        errors.python_script = '脚本必须包含函数体';
      } else {
        delete errors.python_script;
      }
    };

    const validateParamName = (name: string, index: number) => {
      if (!name.trim()) {
        errors[`param_${index}_name`] = '请输入属性名称';
      } else if (!/^[a-zA-Z0-9_]+$/.test(name)) {
        errors[`param_${index}_name`] = '属性名称只能包含英文字母、数字和下划线';
      } else {
        delete errors[`param_${index}_name`];
      }
    };

    // 验证参数中文名称
    const validateParamLabel = (label: string, index: number) => {
      if (!label.trim()) {
        errors[`param_${index}_label`] = '请输入参数中文名称';
      } else {
        delete errors[`param_${index}_label`];
      }
    };

    // 参数管理
    // 添加参数按钮引用
    const addParamButton = ref<HTMLElement>();
    
    const addParameter = () => {
      formData.params.push({
        name: '',
        type: 'string',
        label: '',
        required: false,
        description: '',
        defaultValue: '',
        direction: 0, // 默认设置为输入参数
        apiUrl: ''
      });
      
      // 等待DOM更新后自动滚动到添加参数按钮
      setTimeout(() => {
        if (addParamButton.value) {
          addParamButton.value.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    };

    // 拖拽排序相关状态和方法
    const draggedItemIndex = ref<number | null>(null);
    const dragOverIndex = ref<number | null>(null);

    const onDragStart = (event: DragEvent, index: number) => {
      draggedItemIndex.value = index;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', index.toString());
      }
      // 添加拖拽时的样式类
      setTimeout(() => {
        const target = event.target as HTMLElement;
        if (target) {
          target.classList.add('dragging');
        }
      }, 0);
    };

    const onDragOver = (event: DragEvent, index: number) => {
      event.preventDefault();
      dragOverIndex.value = index;
    };

    const onDrop = (event: DragEvent, dropIndex: number) => {
      event.preventDefault();
      const dragIndex = draggedItemIndex.value;
      
      // 确保有有效的拖拽索引且与放置索引不同
        if (dragIndex !== null && dragIndex !== dropIndex) {
          // 创建参数数组的副本
          const params = [...formData.params];
          // 移除被拖拽的项并在新位置插入
          const [draggedItem] = params.splice(dragIndex, 1);
          params.splice(dropIndex, 0, draggedItem);
          // 更新原始参数数组
          formData.params = params;
          
          // 移除所有参数相关的错误信息
          Object.keys(errors).forEach(key => {
            if (key.startsWith('param_')) {
              delete errors[key];
            }
          });
          
          // 重新验证所有参数
          formData.params.forEach((param, index) => {
            validateParamName(param.name, index);
            validateParamLabel(param.label, index);
          });
      }
      
      // 重置拖拽状态
      draggedItemIndex.value = null;
      dragOverIndex.value = null;
      
      // 移除拖拽样式类
      setTimeout(() => {
        document.querySelectorAll('.param-item.dragging').forEach(el => {
          el.classList.remove('dragging');
        });
        document.querySelectorAll('.param-item.drag-over').forEach(el => {
          el.classList.remove('drag-over');
        });
      }, 0);
    };

    // 拖拽结束时重置状态
    const onDragEnd = () => {
      draggedItemIndex.value = null;
      dragOverIndex.value = null;
      
      setTimeout(() => {
        document.querySelectorAll('.param-item.dragging').forEach(el => {
          el.classList.remove('dragging');
        });
        document.querySelectorAll('.param-item.drag-over').forEach(el => {
          el.classList.remove('drag-over');
        });
      }, 0);
    };

    const removeParameter = (index: number) => {
      formData.params.splice(index, 1);
      // 移除相关的错误信息
      delete errors[`param_${index}_name`];
      delete errors[`param_${index}_options`];
    };


    const onParamTypeChange = (param: any, _index: number) => {
      // 根据参数类型调整默认值
      if (param.type === 'boolean') {
        param.defaultValue = false;
      } else if (param.type === 'number') {
        param.defaultValue = 0;
      } else {
        param.defaultValue = '';
      }      
    };

    // 保存指令
    const handleSave = async () => {
      if (!validateForm()) {
        // 滚动到第一个错误位置
        const firstError = document.querySelector('.error-message');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
      }
      
      try {
        loading.value = true;
        
        // 构建请求数据
        const requestData = {
          name: formData.name,
          description: formData.description,
          icon: formData.icon,
          sort_order: formData.sort_order,
          python_script: formData.python_script,
          category_id: formData.category,
          params: formData.params.map(param => {
            // 创建新对象，只包含需要的属性，不包含options
            return {
              name: param.name,
              type: param.type,
              label: param.label,
              required: param.required,
              description: param.description,
              defaultValue: param.defaultValue,
              direction: param.direction,
              apiUrl: param.apiUrl
            };
          })
        };
        
        emit('save', requestData);
      } catch (error) {
        console.error('保存指令失败:', error);
        ElMessage.error('保存失败，请重试');
      } finally {
        loading.value = false;
      }
    };

    // 取消操作
    const handleCancel = () => {
      resetForm();
      emit('close');
    };

    // 将图标类名转换为组件名
    const getIconComponent = (iconName: string) => {
      // Element Plus图标组件命名规则：el-icon-xxx -> Xxx
      const componentName = iconName.replace('el-icon-', '').split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join('');
      return componentName;
    };

    // 确认图标选择
    const confirmIconSelection = () => {
      if (selectedIcon.value) {
        formData.icon = selectedIcon.value;
      }
      showIconSelector.value = false;
    };


    // 取消图标选择
    const cancelIconSelection = () => {
      selectedIcon.value = '';
      showIconSelector.value = false;
    };

    // 监听指令数据变化
    watch(() => props.instruction, (newValue) => {
      isEdit.value = !!newValue;
      if (newValue) {
        fillFormData(newValue as Instruction);
      } else {
        resetForm();
      }
    }, { immediate: true });

    // 监听可见性变化
    watch(() => props.visible, (newValue) => {
      if (newValue && !props.instruction) {
        resetForm();
      }
    });

    // 组件挂载时加载分类数据
    onMounted(() => {
      loadCategories();
    });

    return {
       localVisible,
       loading,
       categories,
       errors,
       formData,
       validateName,
       validateDescription,
       validateCategory,
       validateScript,
       validateParamName,
       validateParamLabel,
       addParameter,
       removeParameter,
       onParamTypeChange,
       handleSave,
       handleCancel,
       showIconSelector,
       iconSearchKeyword,
       selectedIcon,
       filteredIcons,
       confirmIconSelection,
       cancelIconSelection,
       getIconComponent,
       isEdit,
       draggedItemIndex,
       dragOverIndex,
       onDragStart,
       onDragOver,
       onDrop,
       onDragEnd
     };
  }
});
</script>

<style scoped>
.instruction-form {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

/* 表单区域 */
.form-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e1e8ed;
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.form-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 表单网格 */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* 表单项目 */
.form-item {
  margin-bottom: 2px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.form-label.required::after {
  content: '*';
  color: #ef4444;
  margin-left: 4px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 单选框组样式 */
.radio-group {
  display: flex;
  gap: 20px;
  align-items: center;
}

.radio-option {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 6px;
}

.radio-option input[type="radio"] {
  margin: 0;
  cursor: pointer;
}

.radio-option span {
  font-size: 14px;
  color: #334155;
}

/* 行内单选框样式 */
.form-item.inline-radio {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-item.inline-radio .inline-label {
  margin-bottom: 0;
  white-space: nowrap;
}

.form-item.inline-radio .inline-options {
  flex: 1;
  margin-bottom: 0;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.error-message {
  margin-top: 4px;
  font-size: 12px;
  color: #ef4444;
}

.char-count {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
}

/* 图标选择器 */
.icon-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-preview {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  font-size: 18px;
}

.icon-select-btn {
  padding: 4px 10px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  min-width: 80px;
}

.icon-select-btn:hover {
  background-color: #2563eb;
}

.icon-selector-content {
  max-height: 400px;
  overflow-y: auto;
}

.icon-search {
  margin-bottom: 16px;
}

.icon-list {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 12px;
  padding: 8px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-item:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.icon-item.selected {
  border-color: #3b82f6;
  background-color: #dbeafe;
}

.icon-item i {
  font-size: 12px;
  margin-bottom: 8px;
  color: #374151;
}

.icon-item span {
  position: absolute;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  font-size: 12px;
  text-align: center;
}

.icon-item:hover span {
  opacity: 1;
}

.icon-item {
  position: relative;
}

/* 脚本编辑器 */
.script-editor {
  display: flex;
  gap: 16px;
  position: relative;
}

.script-textarea {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  min-height: 200px;
}

.script-helper {
  width: 200px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
}

.helper-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #2c3e50;
}

.script-helper ul {
  margin: 0;
  padding-left: 16px;
  color: #64748b;
}

.script-helper li {
  margin-bottom: 4px;
  line-height: 1.4;
}

/* 参数配置 */
.empty-params {
  padding: 24px;
  text-align: center;
  color: #64748b;
  background-color: #f8fafc;
  border-radius: 6px;
}

.params-container {
  gap: 16px;
}

.param-item {
  padding: 16px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 10px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.drag-handle {
  cursor: grab;
  color: #999;
  font-size: 16px;
  padding: 4px 8px;
  margin-right: 8px;
  user-select: none;
  transition: color 0.2s;
}

.drag-handle:hover {
  color: #666;
}

.param-item {
  transition: all 0.2s ease;
  border-radius: 4px;
}

.param-item.dragging {
  opacity: 0.6;
  transform: rotate(2deg);
  cursor: grabbing;
}

.param-item.drag-over {
  border: 2px dashed #409eff;
  background-color: #f0f9ff;
}

.param-index {
  font-weight: 500;
  color: #333;
}

.param-index {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.param-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 120px;
  gap: 16px;
  margin-bottom: 2px;
}

.checkbox-item {
  display: flex;
  align-items: flex-end;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.checkbox-wrapper label {
  font-weight: normal;
  margin: 0;
  cursor: pointer;
}

/* 选项配置 */
.options-config {
  margin-top: 8px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.option-input {
  flex: 1;
}

/* 验证辅助信息 */
.validation-helper {
  margin-top: 4px;
}

.validation-helper small {
  color: #94a3b8;
  font-size: 12px;
}

/* 删除参数按钮 */
.delete-param-btn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
  background-color: #fef2f2;
  border: 1px solid #fee2e2;
  color: #ef4444;
}

.delete-param-btn:hover {
  background-color: #fee2e2;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.1);
}

.delete-param-btn:active {
  transform: translateY(0);
}

.delete-param-btn i {
  margin-right: 4px;
}

/* 参数头部样式优化 */
.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.param-index {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-grid,
  .param-form-grid {
    grid-template-columns: 1fr;
  }
  
  .script-editor {
    flex-direction: column;
  }
  
  .delete-param-btn {
    padding: 4px 8px;
    font-size: 11px;
  }
}

/* 添加参数按钮样式优化 */
.add-param-button-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  margin-bottom: 16px;
}

.add-param-button-container .btn-primary {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  background-color: #3b82f6;
  border: 1px solid #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.add-param-button-container .btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.add-param-button-container .btn-primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.add-param-button-container .btn-primary:disabled {
  background-color: #93c5fd;
  border-color: #93c5fd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.add-param-button-container .btn-primary i {
  margin-right: 6px;
}

@media (max-width: 768px) {
  .script-helper {
    width: 100%;
  }
  
  .checkbox-item {
    align-items: flex-start;
    margin-top: 8px;
  }
}
</style>