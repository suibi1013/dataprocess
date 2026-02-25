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
            <div class="form-item">
              <label class="form-label">标签文本</label>
              <div class="input-with-variable" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                <el-input 
                  type="text" 
                  class="form-input"
                  :placeholder="'请输入连线标签文本'"
                  :model-value="props.paramsPanel.params?.label || ''"
                  @update:model-value="updateEdgeLabel"
                ></el-input>
                <el-button 
                  type="primary" round
                  class="variable-select-btn"
                  @click="onToggleVariableSelector('label', 'string')" 
                  title="选择变量"
                  :data-param-name="'label'"
                >
                  x
                </el-button>
              </div>
              <div class="form-help">设置连线的标签文本，点击x按钮可插入变量</div>
            </div>
            <div class="form-item">
              <label class="form-label">逻辑表达式</label>
              <div class="input-with-variable" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                <el-input 
                  type="text" 
                  class="form-input"
                  :placeholder="'请输入逻辑表达式'"
                  :model-value="props.paramsPanel.params?.logic_express || ''"
                  @update:model-value="updateEdgeLogicExpress"
                ></el-input>
                <el-button 
                  type="primary" round
                  class="variable-select-btn"
                  @click="onToggleVariableSelector('logic_express', 'string')" 
                  title="选择变量"
                  :data-param-name="'logic_express'"
                >
                  x
                </el-button>
              </div>
              <div class="form-help">设置连线的逻辑表达式，用于条件判断</div>
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
                <div v-if="(item.param?.display_type === 'number' || item.display_type === 'number')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button 
                    type="primary" round
                    class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'number')" 
                    title="选择变量"
                    :data-param-name="item.param?.name || item.name"
                  >
                    x
                  </el-button>
                </div>

                <!-- 文本输入框 - 复合型输入框 -->
                <div v-else-if="(item.param?.display_type === 'string' || item.display_type === 'string')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button 
                    type="primary" round
                    class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'string')" 
                    title="选择变量"
                    :data-param-name="item.param?.name || item.name"
                  >
                    x
                  </el-button>
                </div>
                
                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.display_type === 'select_excelpath' || item.display_type === 'select_excelpath')"
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
                  <el-button type="success" round class="variable-select-btn" title="选择数据"
                    @click="onHandleManualDataPreview(item.param?.name || item.name)">
                    <el-icon><DocumentChecked /></el-icon>
                  </el-button>
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.display_type === 'boolean' || item.display_type === 'boolean')" class="switch-container" style="margin-bottom: 2px;">
                  <el-switch 
                    v-model="item.value"
                    @change="updateParamValue(item.param?.name || item.name, $event)"
                  ></el-switch>
                </div>

                <!-- 文件上传 (file_upload类型) -->
                <div v-else-if="(item.param?.display_type === 'file_upload' || item.display_type === 'file_upload')" class="upload-container" style="margin-bottom: 2px;">
                  <el-upload 
                    :file-list="item.value ? [{name: onGetFileNameFromPath(item.value), url: item.value}] : []"
                    :auto-upload="false"
                    :on-change="(uploadFile) => onHandleFileUpload(item.param?.name || item.name, { target: { files: [uploadFile.raw] } } as any)"
                    accept=".*"
                  >
                    <el-button type="primary" round>{{ item.value ? '更换文件' : '选择文件' }}</el-button>
                  </el-upload>
                  <div v-if="item.value" class="upload-file-info" style="margin-top: 10px;">
                    {{ onGetFileNameFromPath(item.value) }}
                    <el-button 
                      type="warning" round
                      class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)"
                    >移除</el-button>
                  </div>
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.display_type === 'select_radio' || item.display_type === 'select_radio')" style="margin-bottom: 2px;" :key="`select_radio-${item.param?.name || item.name}`">
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

                <!-- 按钮事件类型 -->
                <div v-else-if="(item.param?.display_type === 'button_event' || item.display_type === 'button_event')" class="button-event-container" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input" 
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button 
                    type="success" round
                    :loading="executingButtons[item.param?.name || item.name]" 
                    @click="onHandleButtonEventClick(item)"
                    style="margin-left: 8px;"
                  >
                    {{ item.param?.label || item.label }}
                  </el-button>
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
                <div v-if="(item.param?.display_type === 'number' || item.display_type === 'number')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
                    disabled
                  >
                    <template #prefix>
                      <!-- 使用 img 标签显示本地图标 -->
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                        disabled
                      />
                    </template>
                  </el-input>
                </div>


                <!-- 文本输入框 - Element Plus复合型输入框 -->
                <div v-else-if="(item.param?.display_type === 'string' || item.display_type === 'string')" class="input-with-variable composite-input"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
                    disabled
                  >
                    <template #prefix>
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                        disabled
                      />
                    </template>
                  </el-input>
                </div>

                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.display_type === 'select_excelpath' || item.display_type === 'select_excelpath')"
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
                    disabled
                  />
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.display_type === 'boolean' || item.display_type === 'boolean')" class="switch-container" style="margin-bottom: 2px;">
                  <el-switch 
                    v-model="item.value"
                    @change="updateParamValue(item.param?.name || item.name, $event)"
                    disabled
                  ></el-switch>
                </div>

                <!-- 文件上传 (file类型) -->
                <div v-else-if="(item.param?.display_type === 'file_upload' || item.display_type === 'file_upload')" class="upload-container" style="margin-bottom: 2px;">
                  <el-upload 
                    :file-list="item.value ? [{name: onGetFileNameFromPath(item.value), url: item.value}] : []"
                    :auto-upload="false"
                    :on-change="(uploadFile) => onHandleFileUpload(item.param?.name || item.name, { target: { files: [uploadFile.raw] } } as any)"
                    accept=".*"
                    disabled
                  >
                    <!-- <el-button type="primary" round>{{ item.value ? '更换文件' : '选择文件' }}</el-button> -->
                  </el-upload>
                  <!-- <div v-if="item.value" class="upload-file-info" style="margin-top: 10px;">
                    {{ onGetFileNameFromPath(item.value) }}
                    <el-button 
                      type="warning" round 
                      class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)"
                    >移除</el-button>
                  </div> -->
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.display_type === 'select_radio' || item.display_type === 'select_radio')" style="margin-bottom: 2px;" :key="`select_radio-output-${item.param?.name || item.name}`">
                  <el-select :model-value="item.value"
                    :placeholder="'请选择' + (item.param?.label || item.label)"
                    class="form-select"
                    :loading="loadingOptions[item.param?.name || item.name]"
                    @update:model-value="updateParamValue(item.param?.name || item.name, $event)"
                    @dropdown-click="() => initFormItemOptions(item)">
                    disabled
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
                <!-- 按钮事件类型 -->
                <div v-else-if="(item.param?.display_type === 'button_event' || item.display_type === 'button_event')" class="button-event-container" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input" 
                    @input="updateParamValue(item.param?.name || item.name, $event)"
                    disabled
                  >
                    <template #prefix>
                      <!-- 使用 img 标签显示本地图标 -->
                      <img 
                        :src="getInputTypeIconPath(item.param?.name || item.name)" 
                        alt="切换输入类型" 
                        class="input-type-toggle-icon" 
                        @click="toggleInputType(item.param?.name || item.name)" 
                        title="切换输入类型（表达式/文本）" 
                        disabled
                      />
                    </template>
                  </el-input>
                  <!-- <el-button 
                    type="success" round 
                    :loading="executingButtons[item.param?.name || item.name]" 
                    @click="onHandleButtonEventClick(item)"
                    style="margin-left: 8px;"
                  >
                    {{ item.param?.label || item.label }}
                  </el-button> -->
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
                <div v-if="(item.param?.display_type === 'number' || item.display_type === 'number')" class="input-with-variable"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 5px;">
                  <el-input 
                    type="number" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button type="primary" round class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'number')" title="选择变量"
                    :data-param-name="item.param?.name || item.name">
                    x
                  </el-button>
                </div>


                <!-- 文本输入框 - Element Plus复合型输入框 -->
                <div v-else-if="(item.param?.display_type === 'string' || item.display_type === 'string')" class="input-with-variable"
                  style="position: relative; display: flex; align-items: center; margin-bottom: 5px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input"
                    style="padding: 0px;"
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button type="primary" round class="variable-select-btn"
                    @click="onToggleVariableSelector(item.param?.name || item.name, 'string')" title="选择变量"
                    :data-param-name="item.param?.name || item.name">
                    x
                  </el-button>
                </div>

                <!-- excel文件路径选择器 (select_excelpath类型) - 使用级联选择器 -->
                <div v-else-if="(item.param?.display_type === 'select_excelpath' || item.display_type === 'select_excelpath')"
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
                  <el-button type="success" round class="variable-select-btn" :disabled="!item.value" title="选择数据"
                    @click="onHandleManualDataPreview(item.param?.name || item.name)">
                    <el-icon><DocumentChecked /></el-icon>
                  </el-button>
                </div>

                <!-- 开关选择器 (boolean类型) -->
                <div v-else-if="(item.param?.display_type === 'boolean' || item.display_type === 'boolean')" class="switch-container">
                  <el-switch 
                    v-model="item.value"
                    @change="updateParamValue(item.param?.name || item.name, $event)"
                  ></el-switch>
                </div>

                <!-- 文件上传 (file类型) -->
                <div v-else-if="(item.param?.display_type === 'file_upload' || item.display_type === 'file_upload')" class="upload-container">
                  <el-upload 
                    :file-list="item.value ? [{name: onGetFileNameFromPath(item.value), url: item.value}] : []"
                    :auto-upload="false"
                    :on-change="(uploadFile) => onHandleFileUpload(item.param?.name || item.name, { target: { files: [uploadFile.raw] } } as any)"
                    accept=".*"
                  >
                    <el-button type="primary" round>{{ item.value ? '更换文件' : '选择文件' }}</el-button>
                  </el-upload>
                  <div v-if="item.value" class="upload-file-info" style="margin-top: 10px;">
                    {{ onGetFileNameFromPath(item.value) }}
                    <el-button 
                      type="warning" round 
                      class="remove-file-btn"
                      @click="updateParamValue(item.param?.name || item.name, null)"
                    >移除</el-button>
                  </div>
                </div>

                <!-- 下拉选择框 -->
                <div v-else-if="(item.param?.display_type === 'select_radio' || item.display_type === 'select_radio')" :key="`select-writeback-${item.param?.name || item.name}`">
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

                <!-- 按钮事件类型 -->
                <div v-else-if="(item.param?.display_type === 'button_event' || item.display_type === 'button_event')" class="button-event-container" style="position: relative; display: flex; align-items: center; margin-bottom: 2px;">
                  <el-input 
                    type="text" 
                    v-model="item.value" 
                    :placeholder="item.param?.placeholder || item.placeholder || '请输入' + (item.param?.label || item.label)" 
                    class="form-input" 
                    @input="updateParamValue(item.param?.name || item.name, $event)"
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
                  <el-button 
                    type="success" round 
                    :loading="executingButtons[item.param?.name || item.name]" 
                    @click="onHandleButtonEventClick(item)"
                    style="margin-left: 8px;"
                  >
                    {{ item.param?.label || item.label }}
                  </el-button>
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
import { DocumentChecked } from '@element-plus/icons-vue';
import { ElNotification } from 'element-plus';
import { ref, computed, watch} from 'vue';
import VariableSelector from './VariableSelector.vue';
import { useDataProcess } from '@/composables/useDataProcess';
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
const executingButtons = ref<Record<string, boolean>>({}); // 用于按钮事件类型控件
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
        result.data.previous_nodes.forEach((node, index) => {
          // 处理节点名称：如果没有名称则使用默认名称，对于重复名称添加索引
          let nodeName = node.node_name || `未命名节点${index}`;
          
          // 确保变量数组存在
          const variables = node.variables ? [...node.variables].map(v => ({ ...v })) : [];
          
          // 为每个节点生成唯一键，避免重复节点名称覆盖
          const uniqueNodeKey = `${nodeName}_${index}`;
          
          // 添加所有节点，无论是否包含变量
          variablesByNode[uniqueNodeKey] = variables;
          initialExpandedNodes[uniqueNodeKey] = true; // 默认展开所有节点
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

// 计算变量选择器的样式
const getVariableSelectorStyle = (_event: any, paramName: string) => {
  // 获取基础样式
  const baseStyle = {
    position: 'fixed', // 使用fixed定位，避免被容器裁剪
    zIndex: 2000,
    background: 'white',
    border: '1px solid #dcdfe6',
    borderRadius: '4px',
    padding: '10px',
    boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)',
    minWidth: '300px',
    maxHeight: '400px',
    overflowY: 'auto'
  };

  try {
    // 使用数据属性定位当前变量选择按钮，这比使用onclick事件更可靠
    const btnElement = document.querySelector(`.variable-select-btn[data-param-name="${paramName}"]`);

    if (btnElement && btnElement instanceof HTMLElement) {
      const btnRect = btnElement.getBoundingClientRect();
      
      // 计算变量选择器的位置，使其显示在触发按钮的正下方
      let top = btnRect.bottom + 5;
      let left = btnRect.left;
      
      // 确保选择器不会超出视口右侧边界
      if (left + 300 > window.innerWidth) {
        left = window.innerWidth - 310;
      }
      
      // 确保选择器不会超出视口底部边界
      if (top + 300 > window.innerHeight) {
        // 如果会超出底部，则显示在按钮正上方
        top = btnRect.top - 305;
      }
      
      // 确保选择器不会超出视口顶部边界
      if (top < 0) {
        top = 10;
      }
      
      // 确保选择器不会超出视口左侧边界
      if (left < 0) {
        left = 10;
      }
      
      return {
        ...baseStyle,
        top: `${top}px`,
        left: `${left}px`
      };
    }
  } catch (error) {
    console.error('计算变量选择器样式失败:', error);
  }

  // 默认样式 - 显示在触发按钮附近
  return {
    ...baseStyle,
    right: '65px',
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
    if (paramName === 'label') { 
      // 获取当前值，采用追加机制
      const currentValue = props.paramsPanel.params?.label || '';
      updateEdgeLabel(currentValue + variableName);
    }
    if (paramName === 'logic_express') { 
      // 获取当前值，采用追加机制
      const currentValue = props.paramsPanel.params?.logic_express || '';
      updateEdgeLogicExpress(currentValue + variableName);
    }
  } else {
    // 节点的情况：获取当前值，采用追加机制
    // const currentValue = props.paramsPanel.params?.[paramName] || '';
    // updateParamValue(paramName, currentValue + variableName);
    // 采用替换机制
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
    nodeData.input_types = intputTypes;
    
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
    logic_express: updatedParams.logic_express,
    paramsPanel: updatedParamsPanel
  });
};

// 更新边逻辑表达式（实时更新，但不保存）
const updateEdgeLogicExpress = (value: string) => {
  if (!props.paramsPanel.selectedEdge) return;
  
  // 更新参数面板的params
  const updatedParams = { ...props.paramsPanel.params, logic_express: value };
  // 获取当前的paramsPanel对象，并更新params属性
  const updatedParamsPanel = {
    ...props.paramsPanel,
    params: updatedParams
  };
  
  // 发出边更新事件
  emit('update-edge', {
    edge: props.paramsPanel.selectedEdge,
    label: updatedParams.label,
    logic_express: value,
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


// 根据api_url获取options数据
const fetchOptionsByApiUrl = async (paramName: string, api_url: string) => {
  if (!api_url) return;
  
  try {
    loadingOptions.value[paramName] = true;
    const result = await httpClient.get(api_url);
    
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
  const api_url = item.param?.api_url || item.api_url;
  // 如果有api_url且尚未加载过，则处理数据
  if (api_url && !dynamicOptions.value[paramName] && !loadingOptions.value[paramName]) {    
    // 检查api_url类型，如果是数组则直接作为options数据
    if (Array.isArray(api_url)) {
      // 直接使用api_url数组作为options数据
      dynamicOptions.value[paramName] = api_url;
    } else if (typeof api_url === 'string') {
      // 先清理字符串，移除所有可能存在的反引号和空格
      let cleanUrl = api_url.trim();
      // 移除所有反引号，不仅仅是开头和结尾的
      cleanUrl = cleanUrl.replace(/`/g, '');
      // 再次清理可能产生的多余空格
      cleanUrl = cleanUrl.trim();
      // 尝试将字符串解析为JSON，看是否是数组格式的options数据
      try {
        // 先尝试标准JSON解析
        const parsedData = JSON.parse(cleanUrl);
        if (Array.isArray(parsedData)) {
          // 如果解析成功且是数组，则作为options数据使用
          dynamicOptions.value[paramName] = parsedData;
          return;
        }
      } catch (error) {
        // 标准JSON解析失败，尝试处理单引号格式的JSON字符串
        try {
          // 替换单引号为双引号，然后再解析
          const normalizedJson = cleanUrl.replace(/'/g, '"');
          const parsedData = JSON.parse(normalizedJson);
          if (Array.isArray(parsedData)) {
            // 如果解析成功且是数组，则作为options数据使用
            dynamicOptions.value[paramName] = parsedData;
            return;
          }
        } catch (secondError) {
          console.error('处理错误时发生异常:', secondError);
        }
      }      
      // 如果是普通字符串则作为API请求接口
      fetchOptionsByApiUrl(paramName, cleanUrl);
    }
  }
};

// 初始化所有表单项的options数据
const initAllFormItemsOptions = () => {
  const allParams = [...(inputParams.value || []), ...(outputParams.value || []), ...(writebackParams.value || [])];
  allParams.forEach(item => {
    // 只处理select和select_excelpath类型的表单项
    if ((item.param?.display_type === 'select_radio' || item.display_type === 'select_radio' || 
         item.param?.display_type === 'select_excelpath' || item.display_type === 'select_excelpath') &&
        (item.param?.api_url || item.api_url)) {
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
      
      // 清空当前的inputTypes
      inputTypes.value = {};
      
      let hasInputTypeData = false;
      
      // 检查是否有新格式的intput_types属性
      if (nodeData.input_types) {
        try {
          // 确保intput_types是对象
          if (typeof nodeData.input_types === 'object' && nodeData.input_types !== null) {
            // 处理表达式类型参数（key为e）
            if (Array.isArray(nodeData.input_types.e)) {
              nodeData.input_types.e.forEach((paramName: string) => {
                inputTypes.value[paramName] = true; // true表示表达式类型
                hasInputTypeData = true;
              });
            }
            // 处理文本类型参数（key为t）
            if (Array.isArray(nodeData.input_types.t)) {
              nodeData.input_types.t.forEach((paramName: string) => {
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
      if (!nodeData.input_types) {
        nodeData.input_types = {
          e: [], // 表达式类型参数列表
          t: []  // 文本类型参数列表
        };
      }
      
      // 确保intput_types格式正确
      if (typeof nodeData.input_types !== 'object' || nodeData.input_types === null) {
        nodeData.input_types = {
          e: [],
          t: []
        };
      }
      if (!Array.isArray(nodeData.input_types.e)) {
        nodeData.input_types.e = [];
      }
      if (!Array.isArray(nodeData.input_types.t)) {
        nodeData.input_types.t = [];
      }
      
      // 如果没有任何输入类型数据，根据当前的inputTypes.value生成
      if (!hasInputTypeData) {
        // 清空intput_types
        nodeData.input_types.e = [];
        nodeData.input_types.t = [];
        
        // 遍历所有参数，根据inputTypes分类
        Object.entries(inputTypes.value).forEach(([name, isExpr]) => {
          if (isExpr) {
            nodeData.input_types.e.push(name);
          } else {
            nodeData.input_types.t.push(name);
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
    }
  }, 0);
}, { immediate: true, deep: true });

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
  let source_data_path;
  // 首先检查输入参数
  const inputParam = inputParams.value.find(inputItem => inputItem.param?.name === paramName);
  if (inputParam) {
    source_data_path = inputParam.value;
  } else {
    // 然后检查输出参数
    const outputParam = outputParams.value.find(outputItem => outputItem.param?.name === paramName);
    if (outputParam) {
      source_data_path = outputParam.value;
    }
  }

  // 使用实际的excel文件路径选择器已选项
  if (!source_data_path) {
    console.warn('No data path selected for preview');
    return; // 如果没有选择路径，不进行预览
  }
  try {
    previewLoading.value = true;
    
    // 保存当前参数名和文件路径
    currentPreviewParamName.value = paramName;
    currentPreviewFilePath.value = source_data_path;
    // 通知父组件显示预览模态框
    emit('show-data-preview', {
      paramName,
      filePath: source_data_path
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

// 处理按钮事件点击
const onHandleButtonEventClick = async (item) => {
  if (!props.paramsPanel.selectedNode) {
    return;
  }
  
  const nodeData = props.paramsPanel.selectedNode.getData();
  if (!nodeData || !nodeData.instructionId) {
    console.error('节点数据无效，缺少指令ID');
    return;
  }
  
  // 获取当前按钮的唯一标识（使用参数名）
  const buttonKey = item.param?.name || item.name;
  // 按钮名称
  const buttonLabel = '<'+(item.param?.label || item.label)+'> ';
  
  // 设置当前按钮为加载状态
  executingButtons.value[buttonKey] = true;
  
  // 注意：ElNotification的position属性只支持预定义的字符串值，不支持自定义坐标
  // 预定义值：'top-right', 'top-left', 'bottom-right', 'bottom-left'
  // 这里我们使用 'top-right' 作为默认值，靠近按钮位置
  const position = 'top-right';
  
  try {
    // 获取节点参数
    const params = props.paramsPanel.params || {};
    
    // 构建请求数据
    const requestData = {
      instruction_id: nodeData.instructionId, // 指令ID
      script_params: params, // Python脚本参数
      input_types: inputTypes.value, // 输入类型，t表示文本，e表示表达式
      event_param_name: buttonKey // 事件参数名称
    };
    
    // 调用执行事件脚本接口
    const result = await httpClient.post('/instruction/event_execute', requestData);
    
    if (result.success) {
      // 将接口返回结果赋值给表单项的文本框
      const responseValue = result.data || '';
      
      // 更新表单项的值
      updateParamValue(buttonKey, responseValue);
      
      // 同时更新当前item的value，确保视图立即更新
      item.value = responseValue;      
      // 显示成功消息
      ElNotification({
        title: '成功',
        message: buttonLabel+result.message || '操作成功！',
        type: 'success',
        duration: 3000,
        position: position || 'top-right',
        offset: 10
      });
    } else {
      // 处理错误响应
      console.error('按钮事件执行失败:', result.message);
      
      // 显示错误消息
      ElNotification({
        title: '失败',
        message: buttonLabel+result.message || '操作失败，请重试！',
        type: 'error',
        duration: 3000,
        position: position || 'top-right',
        offset: 10
      });
    }
  } catch (error) {
    console.error('执行按钮事件时发生错误:', error);
    
    // 显示错误消息
    ElNotification({
      title: '错误',
      message: buttonLabel+error instanceof Error ? error.message : '操作失败，请重试！',
      type: 'error',
      duration: 3000,
      position: position || 'top-right',
      offset: 10
    });
  } finally {
    // 清除当前按钮的加载状态
    executingButtons.value[buttonKey] = false;
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
  padding: 10px;
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
  padding: 0;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.3s;
  box-sizing: border-box;
}

/* 解决下拉选择框外层框问题 - 移除el-select.form-select的额外padding */
.el-select.form-select {
  padding: 0;
  
  /* 确保Element Plus内部输入框有正确的padding */
  :deep(.el-input__inner) {
    padding: 8px 12px;
  }
  
  /* 移除Element Plus默认的内部边框 */
  :deep(.el-input__wrapper) {
    border: none;
    box-shadow: none;
    padding: 0;
  }
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