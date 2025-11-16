from typing import Optional

from PySide6.QtCore import QObject
import pandas as pd
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog, QDialog
import os
import json

from components.dataset_config_dialog import DatasetConfigDialog
from components.log_dialog import LogDialog
from services.apriori_service import AprioriService, DatasetSelection


class PageOneHandler(QObject):
    def __init__(self, parent: 'PageOne', apriori_service: Optional[AprioriService] = None):
        super().__init__(parent)
        self._parent = parent
        self.apriori_service = apriori_service
        self._loaded_file_info = None  # (path, name, size_mb)
        self._cleaning_log_dialog: Optional[LogDialog] = None

    def select_file(self):
        """选择文件的方式"""
        try:
            # 获取项目根目录下的apriori文件夹作为默认路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            default_path = os.path.join(project_root, "Bayesian_1130", "datas")

            file_path, _ = QFileDialog.getOpenFileName(
                self._parent,
                "选择数据文件",
                default_path,
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

        if not self.apriori_service:
            self._parent.on_common_error("Apriori 服务未初始化，无法继续")
            return

        file_path, file_name, file_size_mb, df = result
        self._loaded_file_info = (file_path, file_name, file_size_mb)
        if hasattr(self._parent, 'pushButton_clean'):
            self._parent.pushButton_clean.setEnabled(False)

        selection = self._prompt_dataset_configuration(df)
        if selection is None:
            show_dialog(self._parent, '已取消列配置，未导入数据', '提示')
            return

        try:
            prepared_df = self.apriori_service.configure_dataset(file_path, selection)
        except Exception as e:
            show_dialog(self._parent, f'配置数据集失败: {str(e)}', '错误')
            return

        display_html = self._format_dataframe_html(file_name, file_size_mb, prepared_df, selection, note="原始数据")
        self._parent.textEdit.setHtml(display_html)

        # 发出文件选择信号，通知MainWindow
        self._parent.emit_file_selected(file_path)
        if hasattr(self._parent, 'pushButton_clean'):
            self._parent.pushButton_clean.setEnabled(True)

        if self._parent:
            summary = {
                'target_col': selection.target_col,
                'normal_value': selection.normal_value,
                'numerical_cols': selection.numerical_cols,
                'categorical_cols': selection.categorical_cols,
                'rule_pattern': selection.rule_pattern,
                'all_columns': selection.all_columns,
                'dataset_config': self.apriori_service.get_dataset_config() if self.apriori_service else None,
                'rule_config': self.apriori_service.get_rule_config() if self.apriori_service else None
            }
            self._parent.emit_dataset_config(summary)

        # 显示成功弹窗
        log_message = self._build_confirmation_log(prepared_df, selection)
        show_dialog(self._parent, log_message, '配置完成')

    def clean_data(self):
        """触发数据清洗"""
        if not self.apriori_service or self.apriori_service.raw_dataframe is None:
            show_dialog(self._parent, '请先导入并配置数据集', '提示')
            return
        self._parent.show_state_tooltip('数据清洗中', '正在执行清洗流程，请稍候...')
        if hasattr(self._parent, 'pushButton_clean'):
            self._parent.pushButton_clean.setEnabled(False)
        try:
            task_manager.submit_task(
                self._run_cleaning_task,
                args=(),
                on_success=self._on_cleaning_success,
                on_error=self._on_cleaning_error
            )
        except RuntimeError as e:
            self._parent.close_state_tooltip()
            self._parent.on_common_error(str(e))

    def _run_cleaning_task(self):
        cleaned_df, report, log_text = self.apriori_service.clean_data()
        file_info = self._loaded_file_info
        selection = self.apriori_service.current_selection
        return cleaned_df, report, log_text, file_info, selection

    def _on_cleaning_success(self, result):
        self._parent.close_state_tooltip()
        if hasattr(self._parent, 'pushButton_clean'):
            self._parent.pushButton_clean.setEnabled(True)
        cleaned_df, report, log_text, file_info, selection = result
        if file_info:
            file_name, file_size_mb = file_info[1], file_info[2]
        else:
            file_name, file_size_mb = "数据集", 0

        display_html = self._format_dataframe_html(
            file_name,
            file_size_mb,
            cleaned_df,
            selection,
            note="清洗后数据"
        )
        self._parent.textEdit.setHtml(display_html)
        self._show_cleaning_log(log_text, report)

    def _on_cleaning_error(self, error_message):
        self._parent.close_state_tooltip()
        if hasattr(self._parent, 'pushButton_clean'):
            self._parent.pushButton_clean.setEnabled(True)
        self._parent.on_common_error(f'数据清洗失败: {error_message}')

    def _show_cleaning_log(self, log_text: str, report: Optional[dict]):
        if self._cleaning_log_dialog is None:
            self._cleaning_log_dialog = LogDialog(title="数据清洗日志", parent=self._parent)
        self._cleaning_log_dialog.show()
        self._cleaning_log_dialog.text_edit.clear()
        if log_text.strip():
            self._cleaning_log_dialog.append_log(log_text.strip())
        if report:
            summary = self._format_cleaning_report(report)
            self._cleaning_log_dialog.append_log("\n[清洗报告]\n" + summary)

    def _format_cleaning_report(self, report: dict) -> str:
        lines = []
        original = report.get('original_shape')
        cleaned = report.get('cleaned_shape')
        if original and cleaned:
            lines.append(f"原始数据规模: {original[0]} 行 × {original[1]} 列")
            lines.append(f"清洗后数据规模: {cleaned[0]} 行 × {cleaned[1]} 列")
        if report.get('missing_values'):
            lines.append("缺失值处理: ")
            for col, count in report['missing_values'].items():
                lines.append(f"  - {col}: {count}")
        if report.get('duplicates'):
            lines.append(f"删除重复行: {report['duplicates']} 行")
        if report.get('rows_removed') is not None:
            lines.append(f"共删除行数: {report.get('rows_removed')}")
        if report.get('columns_removed') is not None:
            lines.append(f"共删除列数: {report.get('columns_removed')}")
        improvement = report.get('data_quality_improvement')
        if improvement:
            lines.append("数据质量改善:")
            lines.append(f"  - 缺失值: {improvement.get('missing_values_before')} -> {improvement.get('missing_values_after')}")
            lines.append(f"  - 重复值删除: {improvement.get('duplicates_removed')}")
            lines.append(f"  - 异常值处理特征数: {improvement.get('outliers_processed')}")
        actions = report.get('cleaning_actions') or report.get('actions')
        if actions:
            lines.append("清洗动作:")
            for action in actions:
                lines.append(f"  - {action}")
        if not lines:
            lines.append(json.dumps(report, ensure_ascii=False, indent=2))
        return "\n".join(lines)

    def _prompt_dataset_configuration(self, df) -> Optional[DatasetSelection]:
        dialog = DatasetConfigDialog(df, parent=self._parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_result()
        return None

    @staticmethod
    def _build_confirmation_log(df, selection: DatasetSelection) -> str:
        lines = [
            "✅ 配置已确认！",
            "✅ 数据集配置已更新",
            f"数据加载完成，共 {len(df)} 行",
            f"目标列: {selection.target_col}",
            f"正常值标识: {selection.normal_value}",
        ]
        return "\n".join(lines)

    def _format_dataframe_html(self, file_name, file_size_mb, df, selection: Optional[DatasetSelection] = None, note: Optional[str] = None):
        """将DataFrame格式化为美观的HTML（参考Page 2 与Page 5 样式）"""
        row_count = len(df)
        col_count = len(df.columns)

        # 开始构建HTML
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'

        # 数据配置摘要
        if selection:
            html += '<div style="margin-bottom: 12px; padding: 10px; background: #f3f7ff; border-radius: 6px;">'
            html += '<h3 style="margin: 0 0 6px 0; color: #1b3c87; font-size: 10pt;">⚙️ 数据集配置确认</h3>'
            html += '<ul style="margin: 4px 0; padding-left: 22px; color: #1f2d3d;">'
            html += f'<li><strong>目标列</strong>: {selection.target_col}</li>'
            html += f'<li><strong>正常值</strong>: {selection.normal_value}</li>'
            html += f'<li><strong>数值列</strong>: {", ".join(selection.numerical_cols) or "未选择"}</li>'
            html += f'<li><strong>分类列</strong>: {", ".join(selection.categorical_cols) or "未选择"}</li>'
            html += f'<li><strong>规则模式</strong>: {selection.rule_pattern}</li>'
            html += '</ul></div>'

        # 统计信息（参考Page 2 的渐变背景）
        html += '<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); border-radius: 6px;">'
        html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10pt;">📊 数据集信息</h3>'
        html += '<ul style="margin: 5px 0; padding-left: 25px; color: #34495e;">'
        html += f'<li style="margin: 3px 0;"><strong>文件</strong>: {file_name}（{file_size_mb} MB）</li>'
        html += f'<li style="margin: 3px 0;"><strong>总行数</strong>: {row_count:,} 行</li>'
        html += f'<li style="margin: 3px 0;"><strong>总列数</strong>: {col_count} 列</li>'
        html += f'<li style="margin: 3px 0;"><strong>列名</strong>: {", ".join(df.columns.tolist())}</li>'
        html += '</ul>'
        html += '</div>'

        # 数据预览表格
        preview_rows = min(100, row_count)  # 最多显示100行
        preview_title = f'📝 数据预览（前 {preview_rows} 行）'
        if note:
            preview_title += f' - {note}'
        html += f'<h3 style="margin: 15px 0 10px 0; color: #2c3e50; font-size: 10pt;">{preview_title}</h3>'

        # 创建表格（参考Page 2 的表格样式）
        html += '<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'

        # 表头（参考Page 2 的渐变背景）
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
            # 交替行颜色（参考Page 2）
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
            html += f'<p style="margin: 0; color: #856404; font-size: 9pt;">💡 <strong>提示</strong>: 数据集共 {row_count:,} 行，仅显示前 {preview_rows} 行作为预览。</p>'
            html += '</div>'

        html += '</div>'

        return html

    def _on_load_error(self, error_message):
        """文件加载失败的回调函数"""
        self._parent.close_state_tooltip()
        self._parent.on_common_error(f'处理文件时出错: {error_message}')
