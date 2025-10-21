from PySide6.QtCore import QObject
import pandas as pd
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog
import os

class PageOneHandler(QObject):
    def __init__(self, parent: 'PageOne'):
        super().__init__(parent)
        self._parent = parent

    def select_file(self):
        """选择文件的方法"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self._parent,
                "选择数据文件",
                "E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/apriori",
                "CSV Files (*.csv);;All Files (*.*)"
            )

            if file_path:
                # 修改这里，调用异步处理方法
                self.handle_file_async(file_path)
            else:
                show_dialog(self._parent, '未选择任何文件', '提示')

        except Exception as e:
            show_dialog(self._parent, f'文件选择出错: {str(e)}', '错误')

    def handle_file_async(self, file_path):
        """异步处理选中的文件"""
        self._parent.show_state_tooltip('正在加载文件', '请稍后，大文件可能需要一些时间...')
        try:
            task_manager.submit_task(
                self._read_file_task, 
                args=(file_path,),
                on_success=self._on_load_success,
                on_error=self._on_load_error
            )
        except RuntimeError as e:
            self._parent.close_state_tooltip()
            self._parent.on_common_error(str(e))

    def _read_file_task(self, file_path):
        """在后台线程中读取和处理文件"""
        file_name = os.path.basename(file_path)
        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        
        # 耗时操作
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 将所有需要的数据一并返回
        return (file_path, file_name, file_size_mb, df)

    def _on_load_success(self, result):
        """文件加载成功后的回调函数"""
        self._parent.close_state_tooltip()
        
        file_path, file_name, file_size_mb, df = result

        # 格式化为HTML显示
        display_html = self._format_dataframe_html(file_name, file_size_mb, df)
        self._parent.textEdit.setHtml(display_html)

        # 发出文件选择信号，通知MainWindow
        self._parent.emit_file_selected(file_path)

        # 显示成功弹窗
        message = f'已选择文件:\n文件名: {file_name}\n文件路径: {file_path}\n文件大小: {file_size_mb} MB'
        show_dialog(self._parent, message, '文件选择成功')

    def _format_dataframe_html(self, file_name, file_size_mb, df):
        """将DataFrame格式化为美观的HTML（参考 Page 2 和 Page 5 样式）"""
        row_count = len(df)
        col_count = len(df.columns)
        
        # 开始构建 HTML
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'
        
        # 统计信息（参考 Page 2 的渐变背景）
        html += '<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); border-radius: 6px;">'        
        html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10pt;">📊 数据集信息</h3>'
        html += '<ul style="margin: 5px 0; padding-left: 25px; color: #34495e;">'
        html += f'<li style="margin: 3px 0;"><strong>总行数</strong>: {row_count:,} 行</li>'
        html += f'<li style="margin: 3px 0;"><strong>总列数</strong>: {col_count} 列</li>'
        html += f'<li style="margin: 3px 0;"><strong>列名</strong>: {", ".join(df.columns.tolist())}</li>'
        html += '</ul>'
        html += '</div>'
        
        # 数据预览表格
        preview_rows = min(100, row_count)  # 最多显示100行
        html += f'<h3 style="margin: 15px 0 10px 0; color: #2c3e50; font-size: 10pt;">📝 数据预览（前 {preview_rows} 行）</h3>'
        
        # 创建表格（参考 Page 2 的表格样式）
        html += '<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        
        # 表头（参考 Page 2 的渐变背景）
        html += '<thead style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #2c3e50;">'
        html += '<tr>'
        html += '<th style="padding: 10px 8px; text-align: left; font-weight: bold; font-size: 9pt;">#</th>'  # 行号列
        for col in df.columns:
            html += f'<th style="padding: 10px 8px; text-align: left; font-weight: bold; font-size: 9pt;">{col}</th>'
        html += '</tr>'
        html += '</thead>'
        
        # 表格内容
        html += '<tbody>'
        for idx, (_, row) in enumerate(df.head(preview_rows).iterrows()):
            # 交替行颜色（参考 Page 2）
            row_style = "background-color: #f8f9fa;" if idx % 2 == 0 else "background-color: white;"
            html += f'<tr style="{row_style}">'
            
            # 行号
            html += f'<td style="padding: 10px 8px; color: #7f8c8d; font-weight: bold;">{idx + 1}</td>'
            
            # 数据列
            for col in df.columns:
                value = row[col]
                # 处理过长的文本
                if isinstance(value, str) and len(str(value)) > 50:
                    value = str(value)[:50] + '...'
                html += f'<td style="padding: 10px 8px; color: #2c3e50;">{value}</td>'
            
            html += '</tr>'
        
        html += '</tbody>'
        html += '</table>'
        
        # 如果数据超过预览行数，显示提示
        if row_count > preview_rows:
            html += f'<div style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">'
            html += f'<p style="margin: 0; color: #856404; font-size: 9pt;">💡 <strong>提示</strong>: 数据集共 {row_count:,} 行，仅显示前 {preview_rows} 行作为预览</p>'
            html += '</div>'
        
        html += '</div>'
        
        return html
    
    def _on_load_error(self, error_message):
        """文件加载失败的回调"""
        self._parent.close_state_tooltip()
        self._parent.on_common_error(f'处理文件时出错: {error_message}')