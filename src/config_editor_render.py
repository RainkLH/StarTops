"""
Startops 配置编辑器渲染模块
负责配置文件（JSON文件）渲染编辑页面（HTML）的方法
"""

import re
from typing import Dict, Any, Optional, List
from src.utils.logger import get_logger

logger = get_logger('config_editor_render')


class ConfigEditorRenderer:
    """配置编辑器渲染器"""
    
    @staticmethod
    def render_form_field(
        field_name: str,
        field_value: Any,
        field_meta: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        渲染单个表单字段的HTML代码
        
        Args:
            field_name: 字段名称
            field_value: 字段值
            field_meta: 字段元数据（包含label、type、validation等信息）
            
        Returns:
            str: HTML代码
        """
        if field_meta is None:
            field_meta = {}
        
        label = field_meta.get("label", field_name)
        field_type = field_meta.get("type", "string")
        description = field_meta.get("description", "")
        required = field_meta.get("required", False)
        
        html = f'<div class="form-group">\n'
        html += f'  <label for="{field_name}" class="form-label">\n'
        html += f'    {label}'
        if required:
            html += f' <span class="required">*</span>'
        html += f'\n  </label>\n'
        
        if description:
            html += f'  <div class="form-help">{description}</div>\n'
        
        # 根据类型渲染不同的输入元素
        if field_type == "number":
            html += ConfigEditorRenderer._render_number_input(
                field_name, field_value, field_meta
            )
        elif field_type == "boolean":
            html += ConfigEditorRenderer._render_checkbox(
                field_name, field_value, field_meta
            )
        elif field_type == "select":
            html += ConfigEditorRenderer._render_select(
                field_name, field_value, field_meta
            )
        elif field_type == "textarea":
            html += ConfigEditorRenderer._render_textarea(
                field_name, field_value, field_meta
            )
        else:  # 默认为文本输入
            html += ConfigEditorRenderer._render_text_input(
                field_name, field_value, field_meta
            )
        
        html += '</div>\n'
        return html
    
    @staticmethod
    def _render_text_input(
        field_name: str,
        field_value: Any,
        field_meta: Dict[str, Any]
    ) -> str:
        """渲染文本输入框"""
        attrs = [f'id="{field_name}"', f'name="{field_name}"']
        attrs.append(f'value="{field_value}"' if field_value is not None else 'value=""')
        
        if field_meta.get("required"):
            attrs.append("required")
        
        if "max_length" in field_meta:
            attrs.append(f'maxlength="{field_meta["max_length"]}"')
        
        if "pattern" in field_meta:
            attrs.append(f'pattern="{field_meta["pattern"]}"')
        
        placeholder = field_meta.get("placeholder", "")
        if placeholder:
            attrs.append(f'placeholder="{placeholder}"')
        
        attrs_str = " ".join(attrs)
        return f'  <input type="text" class="form-input" {attrs_str} />\n'
    
    @staticmethod
    def _render_number_input(
        field_name: str,
        field_value: Any,
        field_meta: Dict[str, Any]
    ) -> str:
        """渲染数值输入框"""
        attrs = [f'id="{field_name}"', f'name="{field_name}"', 'type="number"']
        attrs.append(f'value="{field_value}"' if field_value is not None else 'value=""')
        
        if field_meta.get("required"):
            attrs.append("required")
        
        if "min" in field_meta:
            attrs.append(f'min="{field_meta["min"]}"')
        
        if "max" in field_meta:
            attrs.append(f'max="{field_meta["max"]}"')
        
        if "step" in field_meta:
            attrs.append(f'step="{field_meta["step"]}"')
        else:
            attrs.append('step="1"')
        
        attrs_str = " ".join(attrs)
        return f'  <input {attrs_str} class="form-input" />\n'
    
    @staticmethod
    def _render_checkbox(
        field_name: str,
        field_value: Any,
        field_meta: Dict[str, Any]
    ) -> str:
        """渲染复选框"""
        checked = "checked" if field_value else ""
        return (
            f'  <input type="hidden" name="{field_name}" value="false" />\n'
            f'  <input type="checkbox" id="{field_name}" name="{field_name}" '
            f'value="true" class="form-checkbox" {checked} />\n'
        )
    
    @staticmethod
    def _render_select(
        field_name: str,
        field_value: Any,
        field_meta: Dict[str, Any]
    ) -> str:
        """渲染选择框"""
        attrs = [f'id="{field_name}"', f'name="{field_name}"']
        
        if field_meta.get("required"):
            attrs.append("required")
        
        attrs_str = " ".join(attrs)
        html = f'  <select {attrs_str} class="form-select">\n'
        
        options = field_meta.get("options", [])
        for option in options:
            if isinstance(option, dict):
                opt_value = option.get("value")
                opt_label = option.get("label", opt_value)
            else:
                opt_value = opt_label = option
            
            selected = "selected" if opt_value == field_value else ""
            html += f'    <option value="{opt_value}" {selected}>{opt_label}</option>\n'
        
        html += '  </select>\n'
        return html
    
    @staticmethod
    def _render_textarea(
        field_name: str,
        field_value: Any,
        field_meta: Dict[str, Any]
    ) -> str:
        """渲染文本区域"""
        attrs = [f'id="{field_name}"', f'name="{field_name}"']
        
        if field_meta.get("required"):
            attrs.append("required")
        
        rows = field_meta.get("rows", 5)
        attrs.append(f'rows="{rows}"')
        
        attrs_str = " ".join(attrs)
        value_text = str(field_value) if field_value is not None else ""
        return f'  <textarea {attrs_str} class="form-textarea">{value_text}</textarea>\n'
    
    @staticmethod
    def render_form_html(
        config_data: Dict[str, Any],
        meta_data: Optional[Dict[str, Any]] = None,
        form_action: str = "",
        form_id: str = "config-form"
    ) -> str:
        """
        渲染完整的配置编辑表单HTML
        
        Args:
            config_data: 配置数据
            meta_data: 元数据（包含各字段的标签、类型、验证规则等）
            form_action: 表单提交的URL
            form_id: 表单ID
            
        Returns:
            str: 完整的表单HTML代码
        """
        if meta_data is None:
            meta_data = {}
        
        html = f'<form id="{form_id}" method="POST" action="{form_action}" class="config-form">\n'
        
        # 遍历配置数据渲染字段
        for field_name, field_value in config_data.items():
            field_meta = meta_data.get(field_name, {})
            html += ConfigEditorRenderer.render_form_field(
                field_name, field_value, field_meta
            )
        
        # 添加提交和重置按钮
        html += '<div class="form-actions">\n'
        html += '  <button type="submit" class="btn btn-primary">保存配置</button>\n'
        html += '  <button type="reset" class="btn btn-secondary">重置</button>\n'
        html += '</div>\n'
        
        html += '</form>\n'
        return html
    
    @staticmethod
    def validate_field_regex(value: str, pattern: str) -> bool:
        """
        使用正则表达式验证字段值
        
        Args:
            value: 要验证的值
            pattern: 正则表达式模式
            
        Returns:
            bool: 是否匹配
        """
        try:
            return re.match(pattern, str(value)) is not None
        except Exception as e:
            logger.error(f"Regex validation error: {str(e)}")
            return False
    
    @staticmethod
    def escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        text = str(text)
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text
