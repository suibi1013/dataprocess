<template>
  <div class="params-panel">
    <div class="panel-header">
      <h4 class="panel-title">{{ getPanelTitle() }}</h4>

        <!-- 变量选择器弹窗 - 统一配置，同时支持节点参数和连线标签 -->
        <VariableSelector 
          v-if="variableSelectorVisible && (variableSelectorType === 'string' || variableSelectorType === 'number')"
          :visible="variableSelectorVisible"
          :param-name="variableSelectorFor"
          :for-param="variableSelectorFor"
          :param-type="variableSelectorType"
          :search-keyword="variableSearchKeyword"
          :filtered-variables="filteredVariables"
          :expanded-nodes="expandedNodes"
          :hovered-variable="hoveredVariable"
          :selector-style="getVariableSelectorStyle(null, variableSelectorFor)"
          @mouse-leave="() => { variableSelectorVisible = false }"
          @search-input="(value) => { variableSearchKeyword = value }"
          @toggle-tree-node="onToggleTreeNode"
          @select-variable="onSelectVariable"
          @variable-item-mouse-enter="onVariableItemMouseEnter"
          @variable-item-mouse-leave="onVariableItemMouseLeave" />
    </div>
    <div class="panel-body">
      <div class="panel-content">
        <div v-if="!props.paramsPanel.selectedNode && !props.paramsPanel.selectedEdge" class="params-placeholder">
          <i class="el-icon-info"></i>
          <p>请选择画布中的节点或连线来设置参数</p>
        </div>
        <!-- 边标签编辑表单 -->
        <div v-else-if="props.paramsPanel.selectedEdge" class="params-form">
          <div class="param-group">
            <div class="param-group-title">
              <h4>连线标签设置</h4>
            </div>
            <div class="form-item">
              <label class="form-label">标签文本</label>
              <div class="input-with-variable" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                <input type="text" class="form-input"
                  :placeholder="'请输入连线标签文本'"
                  :value="props.paramsPanel.params?.label || ''"
                  @input="updateEdgeLabel(($event.target as HTMLInputElement).value)" />
                <button type="button" class="variable-select-btn"
                  @click="onToggleVariableSelector('label', 'string')" title="选择变量">
                  x
                </button>
              </div>
              <div class="form-help">设置连线的标签文本，点击x按钮可插入变量</div>
            </div>
          </div>
        </div>
        <!-- 节点参数表单 -->
        <div v-else class="params-form">
          <!-- 统一的参数表单 - 适用于所有指令类型 -->
          <div class="param-groups"
            v-if="props.paramsPanel.paramFormItems && props.paramsPanel.paramFormItems.length > 0">
            <!-- 输入参数分组 -->
            <div class="param-group" v-if="inputParams.length > 0">
              <div class="param-group-title">
                <h4>输入参数</h4>
              </div>
              <div class="form-item" v-for="item in inputParams" :key="item.param?.name || item.name">
                <label class="form-label">
                  {{ item.param?.label || item.label }}
                  <span class="required" v-if="item.param?.required || item.required">*</span>
                </label>

                <!-- 数字输入框 - 复合型输入框 -->
                <div v-if="(item.param?.type === 'number' || item.type === 'number')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <!-- 使用 img 标签显示本地图标 -->
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'number')" title="选择变量">
                    x
                  </button>
                </div>

                <!-- 文本输入框 - 复合型输入框 -->
                <div v-else-if="(item.param?.type === 'string' || item.type === 'string')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'string')" title="选择变量">
                    x
                  </button>
                </div>
                
                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.type === 'select_excelpath' || item.type === 'select_excelpath')"
                  class="input-with-variable" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;" :key="`select_excelpath-${item.param?.name || item.name}`">
                  <!-- 获取要使用的options数据 -->
                  <el-cascader 
                    v-model="item.value"
                    :options="convertToCascaderOptions(dynamicOptions[item.param?.name || item.name] || [])"
                    :placeholder="item.param?.placeholder || item.placeholder || '请选择' + (item.param?.label || item.label)"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @change="(value) => updateParamValue(item.param?.name || item.name, value ? value[value.length - 1] : '')"
                    @expand-change="() => initFormItemOptions(item)"
                    separator="/"
                    :props="{ expandTrigger: 'hover'}"
                    popper-class="custom-cascader-popper"
                  />
                  <button type="button" class="variable-select-btn" title="选择数据"
                    @click="onHandleManualDataPreview(item.param?.name || item.name)">
                    <el-icon><DocumentChecked /></el-icon>
                  </button>
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.type === 'boolean' || item.type === 'boolean')" class="switch-container" style="margin-bottom: 2px;">
                  <label class="switch-label">
                    <input type="checkbox" class="switch-input" :checked="!!item.value"
                      @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).checked)" />
                    <span class="switch-slider"></span>
                  </label>
                </div>

                <!-- 文件上传 (file类型) -->
                <div v-else-if="(item.param?.type === 'file' || item.type === 'file')" class="upload-container" style="margin-bottom: 2px;">
                  <label :for="'file-upload-' + (item.param?.name || item.name)" class="upload-button">
                    {{ item.value ? '更换文件' : '选择文件' }}
                  </label>
                  <input :id="'file-upload-' + (item.param?.name || item.name)" type="file" class="upload-input"
                    @change="onHandleFileUpload(item.param?.name || item.name, $event)" />
                  <div v-if="item.value" class="upload-file-info">
                    {{ onGetFileNameFromPath(item.value) }}
                    <button type="button" class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)">移除</button>
                  </div>
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.type === 'select' || item.type === 'select')" style="margin-bottom: 2px;" :key="`select-${item.param?.name || item.name}`">
                  <el-select :model-value="item.value"
                    :placeholder="'请选择' + (item.param?.label || item.label)"
                    class="form-select"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @update:model-value="updateParamValue(item.param?.name || item.name, $event)"
                    @dropdown-click="() => initFormItemOptions(item)">
                    <el-option value="">请选择{{ item.param?.label || item.label }}</el-option>
                    <!-- 优先使用动态获取的options，如果没有则使用item自带的options -->
                    <template v-if="dynamicOptions[item.param?.name || item.name] && dynamicOptions[item.param?.name || item.name].length > 0">
                      <el-option v-for="option in dynamicOptions[item.param?.name || item.name]" :key="option.value" :label="option.label"
                        :value="option.value" />
                    </template>
                    <template v-else>
                      <el-option v-for="option in item.param?.options || item.options" :key="option.value"
                        :value="option.value">
                        {{ option.label }}
                      </el-option>
                    </template>
                  </el-select>
                </div>

                <!-- 列选择器 -->
                <div v-else-if="(item.param?.type === 'column' || item.type === 'column')" class="column-selector" style="margin-bottom: 2px;">
                  <select v-if="!item.param?.multiple && !item.multiple" class="form-select" :value="item.value"
                    @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLSelectElement).value)">
                    <option value="">请选择列</option>
                    <option v-for="column in availableColumns" :key="column" :value="column">
                      {{ column }}
                    </option>
                  </select>

                  <div v-else class="multi-column-selector">
                    <div v-for="column in availableColumns" :key="column" class="column-option">
                      <label class="checkbox-label">
                        <input type="checkbox" :value="column" :checked="(item.value || []).includes(column)"
                          @change="updateMultiColumnValue(item.param?.name || item.name, column, ($event.target as HTMLInputElement).checked)" />
                        <span>{{ column }}</span>
                      </label>
                    </div>
                  </div>
                </div>

                <!-- 文本域 -->
                <div v-else-if="(item.param?.type === 'textarea' || item.type === 'textarea')" class="textarea-with-type-btn" style="position: relative; margin-bottom: 2px;">
                  <!-- 使用 img 标签显示本地图标 -->
                  <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                  <textarea 
                    class="form-textarea"
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)"
                    :value="item.value"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLTextAreaElement).value)"
                    rows="3"></textarea>
                </div>

                <!-- 参数描述信息 -->
                <div class="form-help" v-if="item.param?.description || item.description">
                  {{ item.param?.description || item.description }}
                </div>

                <!-- 参数错误信息 -->
                <div class="form-error" v-if="item.error">
                  {{ item.error }}
                </div>
              </div>
            </div>

            <!-- 输出参数分组 -->
            <div class="param-group" v-if="outputParams.length > 0">
              <div class="param-group-title">
                <h4>输出参数</h4>
              </div>
              <div class="form-item" v-for="item in outputParams" :key="item.param?.name || item.name">
                <!-- 复用原有的表单项渲染逻辑 -->
                <label class="form-label">
                  {{ item.param?.label || item.label }}
                  <span class="required" v-if="item.param?.required || item.required">*</span>
                </label>

                <!-- 数字输入框 - Element Plus复合型输入框 -->
                <div v-if="(item.param?.type === 'number' || item.type === 'number')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <!-- 使用 img 标签显示本地图标 -->
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'number')" title="选择变量">
                    x
                  </button>
                </div>


                <!-- 文本输入框 - Element Plus复合型输入框 -->
                <div v-else-if="(item.param?.type === 'string' || item.type === 'string')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'string')" title="选择变量">
                    x
                  </button>
                </div>

                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.type === 'select_excelpath' || item.type === 'select_excelpath')"
                  class="input-with-variable" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;" :key="`select_excelpath-output-${item.param?.name || item.name}`">
                  <!-- 获取要使用的options数据 -->
                  <el-cascader 
                    v-model="item.value"
                    :options="convertToCascaderOptions(dynamicOptions[item.param?.name || item.name] || [])"
                    :placeholder="item.param?.placeholder || item.placeholder || '请选择' + (item.param?.label || item.label)"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @change="(value) => updateParamValue(item.param?.name || item.name, value ? value[value.length - 1] : '')"
                    @expand-change="() => initFormItemOptions(item)"
                    separator="/"
                    :props="{ expandTrigger: 'hover'}"
                    popper-class="custom-cascader-popper"
                  />
                  <button type="button" class="variable-select-btn" :disabled="!item.value" title="选择数据"
                    @click="onHandleManualDataPreview(item.param?.name || item.name)">
                    <el-icon><DocumentChecked /></el-icon>
                  </button>
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.type === 'boolean' || item.type === 'boolean')" class="switch-container" style="margin-bottom: 2px;">
                  <label class="switch-label">
                    <input type="checkbox" class="switch-input" :checked="!!item.value"
                      @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).checked)" />
                    <span class="switch-slider"></span>
                  </label>
                </div>

                <!-- 文件上传 (file类型) -->
                <div v-else-if="(item.param?.type === 'file' || item.type === 'file')" class="upload-container" style="margin-bottom: 2px;">
                  <label :for="'file-upload-' + (item.param?.name || item.name)" class="upload-button">
                    {{ item.value ? '更换文件' : '选择文件' }}
                  </label>
                  <input :id="'file-upload-' + (item.param?.name || item.name)" type="file" class="upload-input"
                    @change="onHandleFileUpload(item.param?.name || item.name, $event)" />
                  <div v-if="item.value" class="upload-file-info">
                    {{ onGetFileNameFromPath(item.value) }}
                    <button type="button" class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)">移除</button>
                  </div>
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.type === 'select' || item.type === 'select')" style="margin-bottom: 2px;" :key="`select-output-${item.param?.name || item.name}`">
                  <el-select :model-value="item.value"
                    :placeholder="'请选择' + (item.param?.label || item.label)"
                    class="form-select"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @update:model-value="updateParamValue(item.param?.name || item.name, $event)"
                    @dropdown-click="() => initFormItemOptions(item)">
                    <el-option value="">请选择{{ item.param?.label || item.label }}</el-option>
                    <!-- 优先使用动态获取的options，如果没有则使用item自带的options -->
                    <template v-if="dynamicOptions[item.param?.name || item.name] && dynamicOptions[item.param?.name || item.name].length > 0">
                      <el-option v-for="option in dynamicOptions[item.param?.name || item.name]" :key="option.value" :label="option.label"
                        :value="option.value" />
                    </template>
                    <template v-else>
                      <el-option v-for="option in item.param?.options || item.options" :key="option.value"
                        :value="option.value">
                        {{ option.label }}
                      </el-option>
                    </template>
                  </el-select>
                </div>

                <!-- 列选择器 -->
                <div v-else-if="(item.param?.type === 'column' || item.type === 'column')" class="column-selector" style="margin-bottom: 2px;">
                  <select v-if="!item.param?.multiple && !item.multiple" class="form-select" :value="item.value"
                    @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLSelectElement).value)">
                    <option value="">请选择列</option>
                    <option v-for="column in availableColumns" :key="column" :value="column">
                      {{ column }}
                    </option>
                  </select>

                  <div v-else class="multi-column-selector">
                    <div v-for="column in availableColumns" :key="column" class="column-option">
                      <label class="checkbox-label">
                        <input type="checkbox" :value="column" :checked="(item.value || []).includes(column)"
                          @change="onUpdateMultiColumnValue(item.param?.name || item.name, column, ($event.target as HTMLInputElement).checked)" />
                        <span>{{ column }}</span>
                      </label>
                    </div>
                  </div>
                </div>

                <!-- 文本域 -->
                <div v-else-if="(item.param?.type === 'textarea' || item.type === 'textarea')" class="textarea-with-type-btn" style="position: relative; margin-bottom: 2px;">
                  <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                  <textarea 
                    class="form-textarea"
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)"
                    :value="item.value"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLTextAreaElement).value)"
                    rows="3"></textarea>
                </div>

                <!-- 参数描述信息 -->
                <div class="form-help" v-if="item.param?.description || item.description">
                  {{ item.param?.description || item.description }}
                </div>

                <!-- 参数错误信息 -->
                <div class="form-error" v-if="item.error">
                  {{ item.error }}
                </div>
              </div>
            </div>

            <!-- 回写参数分组 -->
            <div class="param-group" v-if="writebackParams.length > 0">
              <div class="param-group-title">
                <h4>回写参数</h4>
              </div>
              <div class="form-item" v-for="item in writebackParams" :key="item.param?.name || item.name">
                <!-- 复用原有的表单项渲染逻辑 -->
                <label class="form-label">
                  {{ item.param?.label || item.label }}
                  <span class="required" v-if="item.param?.required || item.required">*</span>
                </label>

                <!-- 数字输入框 - Element Plus复合型输入框 -->
                <div v-if="(item.param?.type === 'number' || item.type === 'number')" class="input-with-variable"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 5px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'number')" title="选择变量">
                    x
                  </button>
                </div>


                <!-- 文本输入框 - Element Plus复合型输入框 -->
                <div v-else-if="(item.param?.type === 'string' || item.type === 'string')" class="input-with-variable"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 5px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).value)"
                  >
                    <template #prefix>
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                    </template>
                  </el-input>
                  <button type="button" class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'string')" title="选择变量">
                    x
                  </button>
                </div>

                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.type === 'select_excelpath' || item.type === 'select_excelpath')"
                  class="source-data-path-container" style="display: flex; align-items: center;" :key="`select_excelpath-writeback-${item.param?.name || item.name}`">
                  <!-- 获取要使用的options数据 -->
                  <el-cascader 
                    v-model="item.value"
                    :options="convertToCascaderOptions(dynamicOptions[item.param?.name || item.name] || [])"
                    :placeholder="item.param?.placeholder || item.placeholder || '请选择' + (item.param?.label || item.label)"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @change="(value) => updateParamValue(item.param?.name || item.name, value ? value[value.length - 1] : '')"
                    @expand-change="() => initFormItemOptions(item)"
                    separator="/"
                    :props="{ expandTrigger: 'hover'}"
                    popper-class="custom-cascader-popper"
                  />
                  <button type="button" class="variable-select-btn" :disabled="!item.value" title="选择数据"
                    @click="onHandleManualDataPreview(item.param?.name || item.name)">
                    <el-icon><DocumentChecked /></el-icon>
                  </button>
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.type === 'boolean' || item.type === 'boolean')" class="switch-container">
                  <label class="switch-label">
                    <input type="checkbox" class="switch-input" :checked="!!item.value"
                      @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLInputElement).checked)" />
                    <span class="switch-slider"></span>
                  </label>
                </div>

                <!-- 文件上传 (file类型) -->
                <div v-else-if="(item.param?.type === 'file' || item.type === 'file')" class="upload-container">
                  <label :for="'file-upload-' + (item.param?.name || item.name)" class="upload-button">
                    {{ item.value ? '更换文件' : '选择文件' }}
                  </label>
                  <input :id="'file-upload-' + (item.param?.name || item.name)" type="file" class="upload-input"
                    @change="onHandleFileUpload(item.param?.name || item.name, $event)" />
                  <div v-if="item.value" class="upload-file-info">
                    {{ onGetFileNameFromPath(item.value) }}
                    <button type="button" class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)">移除</button>
                  </div>
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.type === 'select' || item.type === 'select')" :key="`select-writeback-${item.param?.name || item.name}`">
                  <el-select :model-value="item.value"
                    :placeholder="'请选择' + (item.param?.label || item.label)"
                    class="form-select"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @update:model-value="updateParamValue(item.param?.name || item.name, $event)"
                    @dropdown-click="() => initFormItemOptions(item)">
                    <el-option value="">请选择{{ item.param?.label || item.label }}</el-option>
                    <!-- 优先使用动态获取的options，如果没有则使用item自带的options -->
                    <template v-if="dynamicOptions[item.param?.name || item.name] && dynamicOptions[item.param?.name || item.name].length > 0">
                      <el-option v-for="option in dynamicOptions[item.param?.name || item.name]" :key="option.value" :label="option.label"
                        :value="option.value" />
                    </template>
                    <template v-else>
                      <el-option v-for="option in item.param?.options || item.options" :key="option.value"
                        :value="option.value">
                        {{ option.label }}
                      </el-option>
                    </template>
                  </el-select>
                </div>

                <!-- 列选择器 -->
                <div v-else-if="(item.param?.type === 'column' || item.type === 'column')" class="column-selector">
                  <select v-if="!item.param?.multiple && !item.multiple" class="form-select" :value="item.value"
                    @change="updateParamValue(item.param?.name || item.name, ($event.target as HTMLSelectElement).value)">
                    <option value="">请选择列</option>
                    <option v-for="column in availableColumns" :key="column" :value="column">
                      {{ column }}
                    </option>
                  </select>

                  <div v-else class="multi-column-selector">
                    <div v-for="column in availableColumns" :key="column" class="column-option">
                      <label class="checkbox-label">
                        <input type="checkbox" :value="column" :checked="(item.value || []).includes(column)"
                          @change="onUpdateMultiColumnValue(item.param?.name || item.name, column, ($event.target as HTMLInputElement).checked)" />
                        <span>{{ column }}</span>
                      </label>
                    </div>
                  </div>
                </div>

                <!-- 文本域 -->
                <div v-else-if="(item.param?.type === 'textarea' || item.type === 'textarea')" class="textarea-with-type-btn" style="position: relative; margin-bottom: 2px;">
                  <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                      />
                  <textarea 
                    class="form-textarea"
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)"
                    :value="item.value"
                    @input="updateParamValue(item.param?.name || item.name, ($event.target as HTMLTextAreaElement).value)"
                    rows="3"></textarea>
                </div>

                <!-- 参数描述信息 -->
                <div class="form-help" v-if="item.param?.description || item.description">
                  {{ item.param?.description || item.description }}
                </div>

                <!-- 参数错误信息 -->
                <div class="form-error" v-if="item.error">
                  {{ item.error }}
                </div>
              </div>
            </div>

            <div class="params-actions" style="margin-bottom: 10px;">
              <el-button type="success" :loading="isExecuting" :disabled="!props.paramsPanel.selectedNode" @click="onHandleRunInstruction">
                <el-icon>
                  <VideoPlay />
                </el-icon>
                运行指令
              </el-button>
            </div>
          </div>

          <!-- 加载状态 -->
          <div class="params-loading" v-if="false">
            <div class="loading-spinner"></div>
            <span>加载参数中...</span>
          </div>

          <!-- 无参数状态 - 只有在确实没有参数时才显示 -->
          <div class="no-params" v-else-if="(inputParams.length === 0) && (outputParams.length === 0)">
            <p>该指令无需配置参数</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElSelect, ElOption, ElButton, ElIcon, ElCascader } from 'element-plus';
import { VideoPlay, DocumentChecked } from '@element-plus/icons-vue';
import { ref, computed, watch } from 'vue';
import VariableSelector from './VariableSelector.vue';
import { useDataProcess } from '@/composables/useDataProcess';
import { instructionService } from '@/services/instructionService';
import { httpClient } from '@/services/httpClient';

// 变量选择器状态

// 变量选择器状态
const variableSelectorVisible = ref(false);
const variableSelectorFor = ref('');
const variableSelectorType = ref('');
const variableSearchKeyword = ref('');
const processVariables = ref<Record<string, Array<{name: string; label: string; value?: any}>>>({});
const hoveredVariable = ref(''); // 用于鼠标悬停效果
const expandedNodes = ref<Record<string, boolean>>({}); // 用于跟踪节点的展开/折叠状态
// 执行状态控制
const isExecuting = ref(false);
// 折叠功能已取消，不再需要isCollapsed状态

// 输入类型状态：键为参数名，值为boolean（true表示表达式，false表示文本）
const inputTypes = ref<Record<string, boolean>>({});

// 获取流程中可用的变量
const onGetProcessVariables = async (selectedNode: any) => {
  if (!selectedNode) {
    processVariables.value = {};
    return;
  }

  // 获取画布中的所有节点和边信息
  const nodes = canvasGraph.value?.getNodes() || [];
  const edges = canvasGraph.value?.getEdges() || [];

  // 构建流程数据
  const flowData = {
    nodes: nodes.map(node => {
      const nodeData = node.getData();
      const position = node.getPosition(); // 获取节点位置信息
      return {
        id: node.id,
        instructionId: nodeData.instructionId,
        x: position.x, // 添加x坐标
        y: position.y, // 添加y坐标
        name: nodeData.label || node.label,
        params: nodeData.params || {}
      };
    }),
    edges: edges.map(edge => ({
      id: edge.id, // 添加边ID
      source: edge.getSourceCellId(),
      target: edge.getTargetCellId()
    }))
  };

  try {
    // 调用后端接口获取前置节点和变量信息
    const result = await httpClient.post('/data-process/get-previous-nodes', {
      flow: flowData,
      target_node_id: selectedNode.id
    });

    if (result.success) {
      // 将previous_nodes数组转换为按节点名称索引的对象
      const variablesByNode: Record<string, Array<{ name: string; label: string; value?: any }>> = {};
      const initialExpandedNodes: Record<string, boolean> = {};

      if (result.data.previous_nodes && Array.isArray(result.data.previous_nodes)) {
        result.data.previous_nodes.forEach(node => {
          // 只添加包含变量的节点
          if (node.node_name && node.variables && node.variables.length > 0) {
            variablesByNode[node.node_name] = node.variables;
            initialExpandedNodes[node.node_name] = true; // 默认展开所有节点
          }
        });
      }

      processVariables.value = variablesByNode;
      expandedNodes.value = initialExpandedNodes;
    } else {
      console.error('获取变量列表失败:', result.message);
      processVariables.value = {};
    }
  } catch (error) {
    console.error('调用后端接口失败:', error);
    processVariables.value = {}
  }
};

// 计算变量选择器的样式，避免被模态框footer遮挡
const getVariableSelectorStyle = (_event: any, paramName: string) => {
  // 获取基础样式
  const baseStyle = {
    position: 'absolute',
    zIndex: 2000,
    background: 'white',
    border: '1px solid #dcdfe6',
    borderRadius: '4px',
    padding: '10px',
    boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)',
    minWidth: '300px',
    maxHeight: '300px',
    overflowY: 'auto',
    right: '65px'
  };

  try {
    // 获取当前变量选择按钮的位置信息
    const btnSelector = `.variable-select-btn[onclick*="${paramName}"]`;
    const btnElement = document.querySelector(btnSelector);

    if (btnElement && btnElement instanceof HTMLElement) {
      const btnRect = btnElement.getBoundingClientRect();
      const modalContainer = document.querySelector('.modal-container');

      if (modalContainer && modalContainer instanceof HTMLElement) {
        const modalRect = modalContainer.getBoundingClientRect();
        const modalFooter = document.querySelector('.modal-footer');
        let footerHeight = 60; // 默认footer高度

        if (modalFooter && modalFooter instanceof HTMLElement) {
          footerHeight = modalFooter.offsetHeight;
        }

        // 计算按钮底部到模态框底部的距离
        const distanceToBottom = modalRect.bottom - btnRect.bottom;

        // 如果距离小于300px（变量选择器的最大高度），则向上弹出
        if (distanceToBottom < 300 + footerHeight) {
          return {
            ...baseStyle,
            bottom: '30px',
            top: 'auto'
          };
        }
      }
    }
  } catch (error) {
    console.error('计算变量选择器样式失败:', error);
  }

  // 默认样式 - 向下弹出
  return {
    ...baseStyle,
    top: '30px'
  };
};

// 过滤后的变量列表
const filteredVariables = computed(() => {
  if (!variableSearchKeyword.value) {
    return processVariables.value;
  }

  const keyword = variableSearchKeyword.value.toLowerCase();
  const filtered: Record<string, Array<{ name: string; label: string; value?: any }>> = {};

  for (const [nodeName, variables] of Object.entries(processVariables.value)) {
    const filteredVariables = variables.filter(variable =>
      variable.name.toLowerCase().includes(keyword) ||
      variable.label.toLowerCase().includes(keyword)
    );

    if (filteredVariables.length > 0) {
      filtered[nodeName] = filteredVariables;
    }
  }

  return filtered;
});

// Props
const props = defineProps({
  paramsPanel: {
    type: Object,
    required: true
  },

  instructionCategories: {
    type: Array,
    default: () => []
  },
  params: {
    type: Object,
    default: () => {}
  }
});

// 注意：在Vue 3的<script setup>中，直接解构props会导致响应性丢失，所以我们保持使用props.xxx的方式

const emit = defineEmits(['update-node', 'update-edge', 'instruction-executed', 'show-data-preview']);

// 使用指令参数组合式函数
// const { } = useInstructionParams(); // 不再使用外部的toggleParamsPanel

// 折叠功能已取消

// 从useDataProcess获取必要的状态
const { loadInstructionList, canvasGraph } = useDataProcess();
// const { canvasGraph } = useDataProcess();

// 切换树节点展开/折叠状态
const onToggleTreeNode = (nodeName: string) => {
  expandedNodes.value[nodeName] = !expandedNodes.value[nodeName];
};

// 已经在上方定义了updateParamValue函数

// 切换变量选择器显示状态
const onToggleVariableSelector = async (paramName: string, paramType: string) => {
  // 首先刷新指令数据，确保指令参数是最新的
  await loadInstructionList();
  
  let targetNode = null;
  
  // 检查是否选中了节点
  if (props.paramsPanel.selectedNode) {
    targetNode = props.paramsPanel.selectedNode;
  }
  // 检查是否选中了连线
  else if (props.paramsPanel.selectedEdge) {
    try {
      const edge = props.paramsPanel.selectedEdge;
      const targetCellId = edge.getTargetCellId(); // 获取连线目标节点的ID
      
      // 使用更安全的方式获取目标节点：通过遍历所有节点查找
      if (canvasGraph.value) {
        const allNodes = canvasGraph.value.getNodes();
        targetNode = allNodes.find(node => node.id === targetCellId) || null;
      }
      
    } catch (error) {
      console.error('获取目标节点时出错:', error);
    }
  }
  
  // 如果没有找到目标节点，显示提示
  if (!targetNode) {
    alert('没有选中有效的节点或连线,请重新选择');
    return;
  }

  // 获取流程中可用的变量，传入目标节点
  await onGetProcessVariables(targetNode);  

  // 强制更新变量选择器状态
  variableSelectorFor.value = paramName;
  variableSelectorType.value = paramType;
  
  // 如果当前是显示状态且参数名相同，则隐藏；否则显示
  if (variableSelectorVisible.value && variableSelectorFor.value === paramName) {
    variableSelectorVisible.value = false;
  } else {
    // 确保变量选择器显示，特别是对于连线的情况
    variableSelectorVisible.value = true;
    
    // 强制Vue更新DOM
    setTimeout(() => {
      variableSelectorVisible.value = true;
    }, 0);
  }
};

// 选择变量
const onSelectVariable = (paramName: string, variableName: string) => {
  // 根据选中的是节点还是边来调用不同的更新函数
  if (props.paramsPanel.selectedEdge) {
    // 边的情况：调用updateEdgeLabel更新标签
    updateEdgeLabel(variableName);
  } else {
    // 节点的情况：调用updateParamValue更新参数
    updateParamValue(paramName, variableName);
  }
  variableSelectorVisible.value = false;
};

// 获取文件名
const onGetFileNameFromPath = (path: string) => {
  return getFileNameFromPath(path);
};

// 切换输入类型（表达式e/文本t）
const toggleInputType = (paramName: string) => {
  inputTypes.value[paramName] = !inputTypes.value[paramName];
  
  // 将输入类型信息保存到节点数据中
  if (props.paramsPanel.selectedNode) {
    const nodeData = props.paramsPanel.selectedNode.getData();
    
    // 转换为新的intput_types格式
    const intputTypes = {
      e: [], // 表达式类型参数列表
      t: []  // 文本类型参数列表
    };
    
    // 遍历所有参数，根据inputTypes分类
    Object.entries(inputTypes.value).forEach(([name, isExpr]) => {
      if (isExpr) {
        intputTypes.e.push(name);
      } else {
        intputTypes.t.push(name);
      }
    });
    
    // 保存到节点数据
    nodeData.intput_types = intputTypes;
    
    // 兼容旧版本，保留inputTypes属性
    if (!nodeData.inputTypes) {
      nodeData.inputTypes = {};
    }
    // 更新对应参数的输入类型
    nodeData.inputTypes[paramName] = inputTypes.value[paramName];
    
    // 保存更新后的节点数据
    props.paramsPanel.selectedNode.setData(nodeData);
  }
};

// 查找指令信息
// const findInstructionById = (instructionId: string) => {
//   for (const category of instructionCategories.value) {
//     const instruction = category.instructions.find(inst => inst.id === instructionId);
//     if (instruction) return instruction;
//   }
//   return null;
// };

// 更新参数值
const updateParamValue = (paramName: string, value: any) => {
  if (!props.paramsPanel.selectedNode) return;
  // 同时更新UI上绑定的item.value，确保视图立即更新
  if (props.paramsPanel.paramFormItems) {
    for (const item of props.paramsPanel.paramFormItems) {
      if ((item.param?.name === paramName) || (item.name === paramName)) {
        item.value = value;
        break;
      }
    }
  }
  // 获取当前节点数据并更新params
  const nodeData = props.paramsPanel.selectedNode.getData();
  const updatedParams = { ...nodeData.params, [paramName]: value };
  // 获取当前的paramsPanel对象，并更新params属性
  const updatedParamsPanel = {
    ...props.paramsPanel,
    params: updatedParams
  };
  // 发出节点更新事件，同时更新params和paramsPanel
  emit('update-node', { 
    params: updatedParams,
    paramsPanel: updatedParamsPanel
  });
};

// 更新边标签（实时更新，但不保存）
const updateEdgeLabel = (value: string) => {
  if (!props.paramsPanel.selectedEdge) return;
  
  // 更新参数面板的params
  const updatedParams = { ...props.paramsPanel.params, label: value };
  
  // 获取当前的paramsPanel对象，并更新params属性
  const updatedParamsPanel = {
    ...props.paramsPanel,
    params: updatedParams
  };
  
  // 发出边更新事件
  emit('update-edge', {
    edge: props.paramsPanel.selectedEdge,
    label: value,
    paramsPanel: updatedParamsPanel
  });
};



// 获取输入参数
const inputParams = computed(() => {
  return props.paramsPanel.paramFormItems?.filter((item: any) => item.param?.direction === 0 || (item.param?.direction === undefined)) || [];
});

// 获取输出参数
const outputParams = computed(() => {
  return props.paramsPanel.paramFormItems?.filter((item: any) => item.param?.direction === 1) || [];
});

// 获取回写参数
const writebackParams = computed(() => {
  return props.paramsPanel.paramFormItems?.filter((item: any) => item.param?.direction === 2) || [];
});


// 根据apiurl获取options数据
const fetchOptionsByApiUrl = async (paramName: string, apiUrl: string) => {
  if (!apiUrl) return;
  
  try {
    loadingOptions.value[paramName] = true;
    const result = await httpClient.get(apiUrl);
    
    if (result && Array.isArray(result)) {
      // 假设返回的是[{value: string, label: string}]格式
      dynamicOptions.value[paramName] = result;
    } else if (result && result.success && Array.isArray(result.data)) {
      // 处理标准API响应格式
      dynamicOptions.value[paramName] = result.data;
    } else if (result && Array.isArray(result.options)) {
      // 处理带有options字段的响应格式
      dynamicOptions.value[paramName] = result.options;
    }
  } catch (error) {
    console.error(`获取${paramName}的options失败:`, error);
    dynamicOptions.value[paramName] = [];
  } finally {
    loadingOptions.value[paramName] = false;
  }
};

// 初始化表单项的options数据
const initFormItemOptions = (item: any) => {
  const paramName = item.param?.name || item.name;
  const apiUrl = item.param?.apiUrl || item.apiUrl;
  // 如果有apiurl且尚未加载过，则获取数据
  if (apiUrl && !dynamicOptions.value[paramName] && !loadingOptions.value[paramName]) {
    fetchOptionsByApiUrl(paramName, apiUrl);
  }
};

// 初始化所有表单项的options数据
const initAllFormItemsOptions = () => {
  const allParams = [...(inputParams.value || []), ...(outputParams.value || []), ...(writebackParams.value || [])];
  allParams.forEach(item => {
    // 只处理select和select_excelpath类型的表单项
    if ((item.param?.type === 'select' || item.type === 'select' || 
         item.param?.type === 'select_excelpath' || item.type === 'select_excelpath') &&
        (item.param?.apiUrl || item.apiUrl)) {          
      initFormItemOptions(item);
    }
  });
};

// 将options数据转换为级联选择器格式
// 注意：现在后端返回的数据已经是标准的级联选择器格式（包含children数组），所以直接返回
const convertToCascaderOptions = (options: any[]) => {
  // 确保返回的是数组，并且进行基本的数据安全检查
  if (!Array.isArray(options)) {
    return [];
  }
  
  // 直接返回原始数据，因为已经是正确的级联格式
  return options;
};

// 监听选中节点变化，自动初始化表单项数据
watch(() => [props.paramsPanel.selectedNode, props.paramsPanel.selectedEdge], () => {
  // 当选中节点或边变化时，延迟初始化以确保表单已经渲染
  setTimeout(() => {
    initAllFormItemsOptions();
    
    // 初始化输入类型
    if (props.paramsPanel.selectedNode) {
      const nodeData = props.paramsPanel.selectedNode.getData();
      console.log(nodeData)
      
      // 清空当前的inputTypes
      inputTypes.value = {};
      
      let hasInputTypeData = false;
      
      // 检查是否有新格式的intput_types属性
      if (nodeData.intput_types) {
        try {
          // 确保intput_types是对象
          if (typeof nodeData.intput_types === 'object' && nodeData.intput_types !== null) {
            // 处理表达式类型参数（key为e）
            if (Array.isArray(nodeData.intput_types.e)) {
              nodeData.intput_types.e.forEach((paramName: string) => {
                inputTypes.value[paramName] = true; // true表示表达式类型
                hasInputTypeData = true;
              });
            }
            // 处理文本类型参数（key为t）
            if (Array.isArray(nodeData.intput_types.t)) {
              nodeData.intput_types.t.forEach((paramName: string) => {
                inputTypes.value[paramName] = false; // false表示文本类型
                hasInputTypeData = true;
              });
            }
          }
        } catch (error) {
          console.error('解析intput_types失败:', error);
        }
      }
      
      // 如果没有新格式数据，检查旧版本的inputTypes格式
      if (!hasInputTypeData && nodeData.inputTypes) {
        try {
          // 兼容旧版本的inputTypes格式
          inputTypes.value = { ...nodeData.inputTypes };
          hasInputTypeData = true;
        } catch (error) {
          console.error('解析inputTypes失败:', error);
        }
      }
      
      // 确保节点数据中存在intput_types属性
      if (!nodeData.intput_types) {
        nodeData.intput_types = {
          e: [], // 表达式类型参数列表
          t: []  // 文本类型参数列表
        };
      }
      
      // 确保intput_types格式正确
      if (typeof nodeData.intput_types !== 'object' || nodeData.intput_types === null) {
        nodeData.intput_types = {
          e: [],
          t: []
        };
      }
      if (!Array.isArray(nodeData.intput_types.e)) {
        nodeData.intput_types.e = [];
      }
      if (!Array.isArray(nodeData.intput_types.t)) {
        nodeData.intput_types.t = [];
      }
      
      // 如果没有任何输入类型数据，根据当前的inputTypes.value生成
      if (!hasInputTypeData) {
        // 清空intput_types
        nodeData.intput_types.e = [];
        nodeData.intput_types.t = [];
        
        // 遍历所有参数，根据inputTypes分类
        Object.entries(inputTypes.value).forEach(([name, isExpr]) => {
          if (isExpr) {
            nodeData.intput_types.e.push(name);
          } else {
            nodeData.intput_types.t.push(name);
          }
        });
      }
      
      // 兼容旧版本，确保存在inputTypes属性
      if (!nodeData.inputTypes) {
        nodeData.inputTypes = {};
        // 初始化旧版本inputTypes
        Object.entries(inputTypes.value).forEach(([name, isExpr]) => {
          nodeData.inputTypes[name] = isExpr;
        });
      }
      
      // 保存更新后的节点数据
      props.paramsPanel.selectedNode.setData(nodeData);
      console.log('更新后的节点数据:', props.paramsPanel.selectedNode.getData())
    }
  }, 0);
}, { immediate: true, deep: true });

// 获取可用列
const availableColumns = computed(() => {
  return props.paramsPanel.availableColumns || [];
});

// 获取节点显示名称
const getNodeDisplayName = (node: any) => {
  if (!node) return '未知节点';
  const nodeData = node.getData ? node.getData() : node;
  // const instruction = findInstructionById(nodeData?.instructionId);
  return nodeData?.label || '未知节点';
};

// 获取面板标题
const getPanelTitle = () => {
  if (props.paramsPanel.selectedEdge) {
    return '连线标签设置';
  } else if (props.paramsPanel.selectedNode) {
    return `参数设置-${getNodeDisplayName(props.paramsPanel.selectedNode)}`;
  }
  return '参数设置';
};

// 更新多列选择值
const updateMultiColumnValue = (paramName: string, columnName: string, checked: boolean) => {
  // 首先检查输入参数
  let currentValue = inputParams.value.find(item => item.name === paramName)?.value || [];
  // 如果输入参数中没有找到，检查输出参数
  if (currentValue.length === 0) {
    currentValue = outputParams.value.find(item => item.name === paramName)?.value || [];
  }

  let newValue;

  if (checked) {
    newValue = [...currentValue, columnName];
  } else {
    newValue = currentValue.filter((col: string) => col !== columnName);
  }

  updateParamValue(paramName, newValue);
};



// 处理文件上传
const onHandleFileUpload = (paramName: string, event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    updateParamValue(paramName, file.name);
    target.value = '';
  }
};

// 从文件路径中提取文件名
const getFileNameFromPath = (path: string): string => {
  if (!path) return '';
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1];
};

// 导入图标资源
import pythonLightIcon from '@/assets/icons/python_light.svg';
import pythonGrayIcon from '@/assets/icons/python_gray.svg';

// 获取输入类型切换图标的路径
const getInputTypeIconPath = (paramName: string): string => {
  return inputTypes.value[paramName] ? pythonLightIcon : pythonGrayIcon;
};

// 直接使用getFileNameFromPath函数，移除重复定义

// 保存当前预览的参数名
const currentPreviewParamName = ref('');
// 保存当前预览的文件路径
const currentPreviewFilePath = ref('');
// 预览加载状态
const previewLoading = ref(false);

// 存储每个表单项的动态options数据
const dynamicOptions = ref<Record<string, Array<{value: string; label: string}>>>({});
// 存储正在加载中的表单项
const loadingOptions = ref<Record<string, boolean>>({});

// 手动触发数据预览
const onHandleManualDataPreview = async (paramName: string) => {
  // 查找参数值
  let sourceDataPath;
  // 首先检查输入参数
  const inputParam = inputParams.value.find(inputItem => inputItem.param?.name === paramName);
  if (inputParam) {
    sourceDataPath = inputParam.value;
  } else {
    // 然后检查输出参数
    const outputParam = outputParams.value.find(outputItem => outputItem.param?.name === paramName);
    if (outputParam) {
      sourceDataPath = outputParam.value;
    }
  }

  // 使用实际的excel文件路径选择器已选项
  if (!sourceDataPath) {
    console.warn('No data path selected for preview');
    return; // 如果没有选择路径，不进行预览
  }
  try {
    previewLoading.value = true;
    
    // 保存当前参数名和文件路径
    currentPreviewParamName.value = paramName;
    currentPreviewFilePath.value = sourceDataPath;
    // 通知父组件显示预览模态框
    emit('show-data-preview', {
      paramName,
      filePath: sourceDataPath
    });
    
    // 直接设置showPreviewModal为true（如果可以访问到）
    if (window.parentDataProcessModal) {
      window.parentDataProcessModal.showPreviewModal = true;
    }
    
  } catch (error) {
    console.error('预览数据时发生错误:', error);
    previewLoading.value = false; // 只有在发生错误时才设置为false
  }
};


// 变量项鼠标进入
const onVariableItemMouseEnter = (variableName: string) => {
  hoveredVariable.value = variableName;
};

// 变量项鼠标离开
const onVariableItemMouseLeave = () => {
  hoveredVariable.value = '';
};

// 查找指令信息
const findInstructionById = (instructionId: string) => {
  // 假设instructionCategories是通过props传递的，如果不是，可以调整这个函数
  if (!props.instructionCategories) {
    console.warn('指令分类数据不可用');
    return null;
  }
  
  for (const category of props.instructionCategories) {
    if (category.instructions && Array.isArray(category.instructions)) {
      const instruction = category.instructions.find(inst => inst.id === instructionId);
      if (instruction) return instruction;
    }
  }
  return null;
};

// 执行指令方法
const onHandleRunInstruction = async () => {
  if (!props.paramsPanel.selectedNode) {
    return;
  }
  
  const nodeData = props.paramsPanel.selectedNode.getData();
  if (!nodeData || !nodeData.instructionId) {
    // 可以添加错误提示
    console.error('节点数据无效，缺少指令ID');
    return;
  }
  
  isExecuting.value = true;
  
  try {
    // 获取节点参数
    const params = props.paramsPanel.params || {};
    
    // 获取指令详情，用于类型转换
    const instruction = findInstructionById(nodeData.instructionId);
    
    // 创建类型转换后的参数对象
    const typedParams: Record<string, any> = { ...params };
    
    // 如果能获取到指令详情，根据参数类型进行转换
    if (instruction && instruction.params) {
      instruction.params.forEach(param => {
        const paramName = param.name;
        const paramValue = params[paramName];
        
        // 确保参数值存在且不为空字符串
        if (paramValue !== undefined && paramValue !== null && paramValue !== '') {
          // 根据参数类型进行转换
          switch (param.type) {
            case 'number':
              // 转换为数字
              typedParams[paramName] = Number(paramValue);
              break;
            case 'boolean':
              // 转换为布尔值
              typedParams[paramName] = paramValue === 'true' || paramValue === true || paramValue === 1;
              break;
            case 'array':
              // 如果是字符串形式的数组，尝试解析
              if (typeof paramValue === 'string' && 
                  (paramValue.startsWith('[') && paramValue.endsWith(']') || 
                   paramValue.includes(','))) {
                try {
                  // 尝试JSON解析
                  if (paramValue.startsWith('[') && paramValue.endsWith(']')) {
                    typedParams[paramName] = JSON.parse(paramValue);
                  } else if (paramValue.includes(',')) {
                    // 逗号分隔的字符串转换为数组
                    typedParams[paramName] = paramValue.split(',').map((item: string) => item.trim());
                  }
                } catch (e) {
                  // 如果解析失败，保持原字符串
                  console.error('数组参数解析失败:', e);
                }
              }
              break;
          }
        }
      });
    }
    
    // 调用后端API来执行指令    
    const result = await instructionService.executeInstruction(nodeData.instructionId, typedParams);
    
    if (result.success && result.data) {
      let details = '';
      // 处理返回的数据结构
      if (result.data) {
        // 将data_result以格式化的JSON字符串显示
        details = JSON.stringify(result.data, null, 2);
      }
      
      // 发送执行结果事件给父组件
      emit('instruction-executed', {
        success: result.success,
        title: result.success ? '执行成功' : '执行失败',
        message: result.message || '指令执行成功！',
        details: details || undefined
      });
    } else {
      // 发送失败结果事件给父组件
      emit('instruction-executed', {
        success: false,
        title: '执行失败',
        message: result.message || '指令执行失败'
      });
    }

  } catch (error) {
    console.error('执行指令失败:', error);
    // 发送错误事件给父组件
    emit('instruction-executed', {
      success: false,
      title: '执行失败',
      message: '指令执行失败',
      details: error instanceof Error ? error.message : '未知错误'
    });
  } finally {
    isExecuting.value = false;
  }
};
</script>

<style scoped>
/* 输入类型按钮样式 */
.input-type-btn {
  width: 30px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #909399;
  transition: all 0.3s;
  margin-right: -1px; /* 消除与输入框的边框间隙 */
}

/* 高亮状态 */
.input-type-btn.active {
  background-color: #409eff;
  border-color: #409eff;
  color: #ffffff;
}

/* 鼠标悬停效果 */
.input-type-btn:hover {
  background-color: #e6f2ff;
  border-color: #c6e2ff;
  color: #409eff;
}

/* 高亮状态下的悬停效果 */
.input-type-btn.active:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* Element Plus按钮的高亮状态样式 */
:deep(.el-button.active) {
  background-color: #84b70c;
  border-color: #cb8a07;
  color: #ffffff;
  /* margin:0 -13px; */
}

/* Element Plus按钮高亮状态下的悬停效果 */
:deep(.el-button.active:hover) {
  background-color: #84b70c;
  border-color: #cb8a07;
}

:deep(.el-input-group__prepend) {
  /* padding: 0 14px !important; */
  background-color: transparent;
  border-right: none;
  border-radius: 4px 0 0 4px;
}
/* 输入框容器样式调整 */
.input-with-variable {
  display: flex;
  align-items: center;
  position: relative;
}

/* 文本域容器样式 */
.textarea-with-type-btn {
  display: flex;
  align-items: flex-start;
  position: relative;
}

/* 文本域样式调整 */
.textarea-with-type-btn .form-textarea {
  margin-left: -1px; /* 消除与按钮的边框间隙 */
}
</style>

<style scoped>
/* 右侧参数面板 */
.params-panel {
  width: 300px;
  background: white;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  /* 保持固定宽度不被压缩 */
  height: 90vh;
  transition: margin-right 0.3s ease;
}

.params-panel.collapsed {
  margin-right: -280px;
}

.params-panel .panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.params-panel .panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.panel-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  color: #8c8c8c;
  transition: all 0.2s ease;
}

.panel-toggle:hover {
  background: #f0f0f0;
  color: #595959;
}

.params-panel .panel-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  /* 解决flex子元素的min-height默认值问题 */
}

.params-panel .panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
  /* 确保在flex布局中内容可以正确滚动 */
  max-height: calc(100% - 120px);
  /* 相对于父容器高度，减去头部和底部的高度 */
}

.params-footer {
  padding: 16px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
}

.params-actions {
  display: flex;
  justify-content: flex-end;
}

/* 参数表单样式增强 */
.params-form .form-item {
  margin-bottom: 16px;
}

/* 参数分组样式 */
.param-group {
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
}

.param-group-title {
  background: #fafafa;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
}

.param-group-title h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.param-group>.form-item {
  padding: 8px;
  margin-bottom: 0;
  border-bottom: 1px solid #f5f5f5;
}

.param-group>.form-item:last-child {
  border-bottom: none;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-label .required {
  color: #ff4d4f;
  margin-left: 2px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 变量选择器样式 */
.input-with-variable {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-with-variable .form-input {
  flex: 1;
}

.variable-select-btn {
  width: 32px;
  height: 32px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

/* 输入类型切换图标样式 */
.input-type-toggle-icon {
  width: 18px;
  height: 18px;
  cursor: pointer;
  margin-right: 8px;
  vertical-align: middle;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.variable-select-btn:hover {
  background: #40a9ff;
}

.variable-select-btn:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
  opacity: 0.6;
}

.variable-selector {
  position: relative;
  margin-top: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.variable-search {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.variable-search-input {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.variable-tree {
  max-height: 200px;
  overflow-y: auto;
}

.variable-node-group {
  margin-bottom: 4px;
}

.variable-node-title {
  padding: 8px 12px;
  background: #f5f5f5;
  font-weight: 500;
  font-size: 13px;
  color: #333;
  border-bottom: 1px solid #e8e8e8;
}

/* 树形结构样式 */
.tree-node-header {
  display: flex;
  align-items: center;
  user-select: none;
}

.tree-expand-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  text-align: center;
  line-height: 16px;
  font-size: 10px;
  transition: transform 0.2s;
  color: #606266;
}

.tree-expand-icon.expanded {
  color: #1890ff;
}

.tree-node-children {
  transition: all 0.3s ease;
}

.variable-item {
  padding: 6px 12px 6px 24px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.2s;
}

.variable-item:hover {
  background: #f0f8ff;
  color: #1890ff;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.column-selector {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 8px;
}

.multi-column-selector {
  max-height: 120px;
  overflow-y: auto;
}

.column-option {
  margin-bottom: 6px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  font-size: 13px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
  width: auto;
}

.form-help {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.form-error {
  margin-top: 4px;
  font-size: 12px;
  color: #ff4d4f;
  line-height: 1.4;
}

/* 开关样式 */
.switch-container {
  display: flex;
  align-items: center;
  margin-top: 4px;
}

.switch-label {
  display: inline-block;
  position: relative;
  width: 48px;
  height: 24px;
}

.switch-input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.switch-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

.switch-input:checked+.switch-slider {
  background-color: #1890ff;
}

.switch-input:checked+.switch-slider:before {
  transform: translateX(24px);
}

/* 文件上传样式 */
.upload-container {
  margin-top: 4px;
}

.upload-input {
  display: none;
}

.upload-button {
  display: inline-block;
  padding: 6px 12px;
  background-color: #f0f0f0;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.upload-button:hover {
  background-color: #e6f7ff;
  border-color: #91d5ff;
}

.upload-file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background-color: #f0f8ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  margin-top: 4px;
  font-size: 14px;
}

.remove-file-btn {
  padding: 2px 8px;
  background-color: #f5222d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.remove-file-btn:hover {
  background-color: #ff4d4f;
}

.params-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
  font-size: 13px;
}

/* 级联选择器固定宽度样式 */
:global(.custom-cascader-popper .el-cascader-menu) {
  min-width: 200px !important;
  width: 200px !important;
  overflow: hidden;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f0f0f0;
  border-top: 2px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

.no-params {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 13px;
}

.params-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 16px;
  text-align: center;
  color: #8c8c8c;
}

.params-placeholder i {
  font-size: 32px;
  opacity: 0.5;
}

.params-placeholder p {
  margin: 0;
  font-size: 14px;
}

.params-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.params-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.params-actions .el-button {
  padding: 8px 16px;
  font-size: 14px;
}

.execution-result {
  margin-top: 16px;
}

.result-details {
  margin-top: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.result-details pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
  overflow-x: auto;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}


</style>