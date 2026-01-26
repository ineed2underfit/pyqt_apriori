from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QVBoxLayout,
    QWidget,
    QScrollArea,
)
from common.utils import show_dialog, get_data_directory, resolve_bayesian_path
from common.config import cfg
from components.bar import ProgressInfoBar
from components.log_dialog import LogDialog
from workers.prediction_worker import PredictionWorker, RESULT_DIR
import os
import re
import json

class PageFourHandler(QObject):
    def __init__(self, parent: 'Page4'):
        super().__init__(parent)
        self._parent = parent
        self.test_data_path = None
        self.thread = None
        self.worker = None
        self.loading_bar = None
        self.log_dialog = None
        self._last_single_input = None

    # --- 批量评估功能 ---
    def select_test_file(self):
        """打开文件对话框，让用户选择测试数据集"""
        try:
            default_dir = get_data_directory()
            file_path, _ = QFileDialog.getOpenFileName(
                self._parent, "选择测试数据文件", default_dir, "CSV Files (*.csv);;All Files (*.*)"
            )
            if file_path:
                self.test_data_path = file_path
                self._parent.textEdit_3.setText(f"已选择测试文件进行批量评估：\n{file_path}")
                self._parent.pushButton_assessment.setEnabled(True)
                self._notify_page5_dataset(file_path)
        except Exception as e:
            show_dialog(self._parent, f'文件选择出错: {str(e)}', '错误')

    def start_batch_assessment(self):
        """开始批量质量评估预测"""
        if not self.test_data_path:
            show_dialog(self._parent, "请先导入测试数据集！", "错误")
            return
        self._run_prediction(self.test_data_path)

    # --- 单次评估功能 ---
    def assess_single_instance(self):
        """弹窗输入单条数据并触发预估"""
        config_info = self._get_dataset_config_info()
        if not config_info:
            show_dialog(self._parent, "请先在数据导入页面配置数据集", "提示")
            return
        dialog = SinglePredictionDialog(self._parent, config_info, initial_data=self._last_single_input)
        if dialog.exec() == QDialog.Accepted:
            data_dict = dialog.get_data()
            self._last_single_input = dict(data_dict)
            self._run_prediction(data_dict)

    # --- 公共的执行和回调逻辑 ---
    def _run_prediction(self, data_payload):
        """通用的预测执行函数，根据传入数据类型启动不同模式"""
        print("--- _run_prediction 方法被调用 ---") # DEBUG
        main_window = self._parent.window()
        model_path = main_window.model_pkl_path

        if not os.path.exists(model_path):
            show_dialog(self._parent, f"模型文件不存在，请先在Page3中构建贝叶斯网络。\n路径: {model_path}", "错误")
            return

        history_data_path = None
        if isinstance(data_payload, dict):
            history_data_path = getattr(main_window, "dataset_path", None)
            if not history_data_path:
                show_dialog(self._parent, "请先在 Page1 导入并配置数据集", "提示")
                return

        # 禁用所有按钮
        self._parent.pushButton_import.setEnabled(False)
        self._parent.pushButton_assessment.setEnabled(False)
        self._parent.pushButton_solely.setEnabled(False)
        
        # 如果是单次预测，初始化进度条
        if isinstance(data_payload, dict):
            if hasattr(self._parent, 'progressBar'):
                self._parent.progressBar.setValue(0)
                self._parent.progressBar.setVisible(True)
        else:
            # 批量预测提示（非阻塞）
            self.loading_bar = ProgressInfoBar("批量预测", "正在进行批量预测...", self._parent)
            self.loading_bar.show()
            if cfg.page4_debug_log.value:
                self.log_dialog = LogDialog(title="批量预测日志", parent=self._parent)
                self.log_dialog.show()

        self.thread = QThread()
        self.worker = PredictionWorker(model_path, data_payload, history_data_path=history_data_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.batch_finished.connect(self.on_batch_assessment_finished)
        self.worker.single_prediction_finished.connect(self.on_single_assessment_finished)
        self.worker.progress_updated.connect(self.on_progress_updated)  # 连接进度信号
        self.worker.error.connect(self.on_assessment_error)
        self.worker.log_message.connect(self._handle_log_message)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_batch_assessment_finished(self, report_text, cm_path):
        """批量评估成功的回调"""
        html = '<div style="font-size: 10pt; line-height: 1.6; color: #2c3e50;">'
        html += '<div style="padding: 10px 0; border-bottom: 2px solid #3498db; margin-bottom: 10px;">'
        html += '<span style="font-size: 12pt; font-weight: bold;">📋 批量质量评价报告</span>'
        html += '</div>'

        html += '<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: Consolas, Menlo, monospace; font-size: 9pt; background: #f7f9fb; padding: 10px; border-radius: 6px; border: 1px solid #e3e9ef;">'
        html += self._escape_html(report_text)
        html += '</pre>'

        if cm_path and os.path.exists(cm_path):
            img_path = cm_path.replace("\\", "/")
            html += '<div style="margin-top: 12px; text-align:center;">'
            html += '<div style="margin: 6px 0 8px 0; font-weight: bold; color: #34495e;">🧭 混淆矩阵</div>'
            html += (f'<img src="file:///{img_path}" alt="confusion_matrix" '
                     f'style="max-width:90%; height:auto; border:1px solid #e3e9ef; border-radius:6px;" />')
            html += '</div>'

        html += '</div>'

        self._parent.textEdit_3.setHtml(html)
        show_dialog(self._parent, "质量评估完成！", "成功")
        self.cleanup_thread()

    @staticmethod
    def _escape_html(text: str) -> str:
        """简单HTML转义，防止报告中的符号影响展示。"""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    def on_progress_updated(self, progress):
        """进度更新回调"""
        if hasattr(self._parent, 'progressBar'):
            self._parent.progressBar.setValue(progress)
    
    def on_single_assessment_finished(self, prediction_result, input_data_dict, probability_dist):
        """单次评估成功的回调"""
        config_info = self._get_dataset_config_info() or {}
        dataset_config = config_info.get('dataset_config') or {}
        feature_names = dataset_config.get('feature_names') or {}
        column_order = config_info.get('categorical_cols', []) + config_info.get('numerical_cols', [])

        predicted_status = prediction_result or "未知"
        normal_value = config_info.get('normal_value') or dataset_config.get('normal_value')
        report_filename = "health_assessment_single_report.txt" if normal_value and predicted_status == normal_value \
            else "fault_diagnosis_single_report.txt"
        report_text, report_error, report_path = self._read_report_text(report_filename)

        probability_items = sorted(probability_dist.items(), key=lambda kv: kv[1], reverse=True) if probability_dist else []

        output = '<div style="font-size: 10pt; line-height: 1.6;">'
        output += '<p style="font-size: 11pt; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px;">⚡ 单次故障概率评估结果</p>'

        if config_info:
            output += '<div style="margin: 8px 0 14px 0; padding: 10px; background: #f5f7fb; border: 1px solid #dfe6f0; border-radius: 6px;">'
            output += f'<p style="margin: 0;"><strong>目标列：</strong>{config_info.get("target_col", "-")} &nbsp; '
            output += f'<strong>正常值：</strong>{config_info.get("normal_value", "-")} &nbsp; '
            output += f'<strong>规则模式：</strong>{config_info.get("rule_pattern", "-")}</p>'
            output += '</div>'

        ordered_items = []
        seen = set()
        for col in column_order:
            if col in input_data_dict and col not in seen:
                ordered_items.append((col, input_data_dict[col]))
                seen.add(col)
        for col, value in input_data_dict.items():
            if col not in seen:
                ordered_items.append((col, value))
                seen.add(col)

        output += '<p style="font-size: 10.5pt; font-weight: bold; color: #34495e; margin-top: 12px;">📊 输入数据：</p>'
        output += '<table style="width: 100%; border-collapse: collapse; margin-top: 8px;">'
        for key, value in ordered_items:
            display_name = feature_names.get(key, key)
            output += '<tr style="border-bottom: 1px solid #ecf0f1;">'
            output += f'<td style="padding: 6px; font-weight: bold; color: #7f8c8d; width: 40%;">{display_name}</td>'
            output += f'<td style="padding: 6px; color: #2c3e50;">{value}</td>'
            output += '</tr>'
        output += '</table>'

        if normal_value and predicted_status == normal_value:
            result_color = "#27ae60"
            result_bg_color = "#d5f4e6"
            result_border_color = "#2ecc71"
            result_icon = "🟢"
        else:
            result_color = "#e74c3c"
            result_bg_color = "#fef5e7"
            result_border_color = "#f39c12"
            result_icon = "🔴"

        output += (
            f'<p style="font-size: 12pt; font-weight: bold; color: {result_color}; margin-top: 15px; padding: 12px; '
            f'background-color: {result_bg_color}; border-left: 5px solid {result_border_color}; border-radius: 5px;">'
            f'{result_icon} 预测故障类型：<span style="color: {result_color}; font-size: 13pt;">{predicted_status}</span></p>'
        )

        if probability_items:
            output += '<div style="margin-top: 15px;">'
            output += '<p style="font-size: 10.5pt; font-weight: bold; color: #34495e; margin-bottom: 8px;">📈 故障类型概率分布：</p>'
            output += '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #e9ecef;">'
            for fault_type, prob in probability_items:
                if not isinstance(prob, (int, float)):
                    continue
                if prob > 0.5:
                    bar_color = "#28a745"
                elif prob > 0.3:
                    bar_color = "#ffc107"
                else:
                    bar_color = "#dc3545"
                bar_width = prob * 100
                prob_text = f'{prob * 100:.2f}%'
                output += '<div style="margin-bottom: 6px;">'
                output += '<div style="display: flex; align-items: center; margin-bottom: 3px;">'
                output += f'<span style="font-size: 9pt; color: #2c3e50; width: 120px; display: inline-block;">{fault_type}</span>'
                output += f'<span style="font-size: 9pt; color: #495057; margin-left: 8px; min-width: 80px;">{prob_text}</span>'
                output += '</div>'
                output += '<div style="background-color: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">'
                output += f'<div style="background-color: {bar_color}; height: 100%; width: {bar_width}%; transition: width 0.3s ease;"></div>'
                output += '</div>'
                output += '</div>'
            output += '</div>'
            output += '</div>'

        if report_error:
            output += f'<p style="color: #e74c3c;">⚠️ 读取 {os.path.basename(report_path)} 时出错: {self._escape_html(report_error)}</p>'
        elif report_text:
            output += '<div style="margin-top: 20px;">'
            output += '<p style="font-size: 10.5pt; font-weight: bold; color: #2c3e50;">📄 评估报告</p>'
            output += '<pre style="white-space: pre-wrap; word-break: break-word; background: #f7f9fb; padding: 12px; border-radius: 6px; border: 1px solid #dfe6ef;">'
            output += self._escape_html(report_text)
            output += '</pre></div>'
        else:
            output += f'<p style="color: #999; margin-top: 12px;">未找到 {os.path.basename(report_path)}，已展示实时预测结果。</p>'

        output += '</div>'

        self._parent.textEdit_solely.setHtml(output)
        self.cleanup_thread()
    def on_assessment_error(self, error_message):
        """评估失败的通用回调"""
        show_dialog(self._parent, f"评估失败: {error_message}", "错误")
        self.cleanup_thread()

    def _handle_log_message(self, message: str):
        if self.log_dialog:
            self.log_dialog.append_log(message)

    def cleanup_thread(self):
        """清理线程"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self.loading_bar:
            self.loading_bar.hide()
            self.loading_bar = None
        if self.log_dialog:
            self.log_dialog.append_log("=== 批量预测流程已结束 ===")
            self.log_dialog = None
        if self._parent:
            self._parent.pushButton_import.setEnabled(True)
            # 只有在选择了测试文件后，才重新启用批量评估按钮
            if self.test_data_path:
                self._parent.pushButton_assessment.setEnabled(True)
            self._parent.pushButton_solely.setEnabled(True)
            # 隐藏进度条
            if hasattr(self._parent, 'progressBar'):
                self._parent.progressBar.setVisible(False)

    def _read_report_text(self, report_filename: str):
        report_path = os.path.join(RESULT_DIR, report_filename)
        if not os.path.exists(report_path):
            return None, None, report_path
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return f.read(), None, report_path
        except Exception as exc:
            return None, str(exc), report_path

    def _parse_single_report(self, report_text: str):
        data = {
            'predicted_status': None,
            'key_parameters': '',
            'probabilities': []
        }
        if not report_text:
            return data

        lines = report_text.splitlines()
        reading_probs = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if reading_probs:
                    reading_probs = False
                continue
            if stripped.startswith("最可能的状态是"):
                match = re.search(r"最可能的状态是:\s*(.+?)，概率为\s*([0-9.]+)", stripped)
                if match:
                    data['predicted_status'] = match.group(1).strip()
                continue
            if stripped.startswith("需要特别关注的参数为"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    data['key_parameters'] = parts[1].strip()
                continue
            if "各状态的预测概率" in stripped:
                reading_probs = True
                continue
            if reading_probs:
                cleaned = stripped.lstrip("•-*→🎯").strip()
                match = re.match(r"(.+?):\s*([0-9.]+)", cleaned)
                if match:
                    label = match.group(1).strip()
                    prob = float(match.group(2))
                    data['probabilities'].append((label, prob))
                    continue

        return data

    def _get_dataset_config_info(self):
        """优先使用已缓存配置，缺失时回退到分箱配置文件"""
        main_window = self._parent.window()
        config_info = getattr(main_window, "dataset_config_info", None)
        if config_info:
            return config_info

        disk_info = self._load_dataset_config_from_disk()
        if disk_info:
            setattr(main_window, "dataset_config_info", disk_info)
        return disk_info

    def _load_dataset_config_from_disk(self):
        """从最新的配置文件载入列信息"""
        candidate_paths = [
            resolve_bayesian_path("result", "apriori_results", "完整数据配置.json"),
            resolve_bayesian_path("result", "apriori_results", "分箱配置.json"),
        ]
        config_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not config_path:
            return None
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return None

        metadata = data.get('metadata', {})
        dataset_config = metadata.get('dataset_config') or data.get('dataset_config') or {}
        column_stats = metadata.get('column_stats') or data.get('column_stats') or {}
        rule_config = metadata.get('rule_config') or data.get('rule_config') or {}

        return {
            'dataset_config': dataset_config,
            'column_stats': column_stats,
            'categorical_cols': dataset_config.get('categorical_cols', []),
            'numerical_cols': dataset_config.get('numerical_cols', []),
            'target_col': dataset_config.get('target_col'),
            'normal_value': dataset_config.get('normal_value'),
            'rule_pattern': rule_config.get('rule_pattern'),
        }



    def _notify_page5_dataset(self, dataset_path: str):
        main_window = self._parent.window()
        page5 = getattr(main_window, 'page5', None)
        handler = getattr(page5, 'handler', None) if page5 else None
        if handler and hasattr(handler, 'update_device_options_from_path'):
            handler.update_device_options_from_path(dataset_path)

class SinglePredictionDialog(QDialog):
    """根据 Page1 配置动态生成的单次预测输入弹窗"""

    def __init__(self, parent=None, dataset_config_info=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("单次质量评价")
        self.setModal(True)
        self.resize(480, 520)
        self.setMinimumWidth(420)

        self.dataset_config_info = dataset_config_info or {}
        self.dataset_config = self.dataset_config_info.get('dataset_config') or {}
        self.column_stats = self.dataset_config_info.get('column_stats') or {}
        self.feature_names = self.dataset_config.get('feature_names') or {}
        self.numerical_cols = (
            self.dataset_config.get('numerical_cols')
            or self.dataset_config_info.get('numerical_cols')
            or []
        )
        self.categorical_cols = (
            self.dataset_config.get('categorical_cols')
            or self.dataset_config_info.get('categorical_cols')
            or []
        )
        self.target_col = self.dataset_config.get('target_col') or self.dataset_config_info.get('target_col')
        self.normal_value = self.dataset_config.get('normal_value') or self.dataset_config_info.get('normal_value')

        self.categorical_inputs = {}
        self.numeric_inputs = {}
        self.initial_data = initial_data or {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel("请按照数据导入页面中选择的列填写本次评估数据。")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        if self.target_col:
            summary = QLabel(
                f"<b>目标列</b>：{self.target_col}&nbsp;&nbsp;"
                f"<b>正常值</b>：{self.normal_value or '-'}&nbsp;&nbsp;"
                f"<b>规则模式</b>：{self.dataset_config_info.get('rule_pattern', '-')}"
            )
            summary.setWordWrap(True)
            layout.addWidget(summary)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        if not self.categorical_cols and not self.numerical_cols:
            placeholder = QLabel("暂未获取到可填写的列，请先在 Page1 完成数据集配置。")
            placeholder.setWordWrap(True)
            self.form_layout.addRow(placeholder)
        else:
            for col in self.categorical_cols:
                combo = self._create_category_field(col)
                self.form_layout.addRow(self._format_label(col, is_categorical=True), combo)
                self.categorical_inputs[col] = combo

            for col in self.numerical_cols:
                spin = self._create_numeric_field(col)
                self.form_layout.addRow(self._format_label(col, is_categorical=False), spin)
                self.numeric_inputs[col] = spin

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _format_label(self, column: str, is_categorical: bool) -> str:
        friendly = self.feature_names.get(column, column)
        if friendly and friendly != column:
            base = f"{friendly}（{column}）"
        else:
            base = column
        suffix = "（分类）" if is_categorical else "（数值）"
        return f"{base}{suffix}"

    @staticmethod
    def _natural_sort(values):
        import re

        def sort_key(value):
            text = str(value)
            match = re.search(r"(\\d+)", text)
            if not match:
                return (1, text)
            return (0, int(match.group(1)), text)

        return sorted(values, key=sort_key)

    def _create_category_field(self, column: str) -> QComboBox:
        combo = QComboBox(self)
        stats = self.column_stats.get('categorical', {}).get(column, {})
        values = stats.get('values', [])
        if values:
            sorted_values = self._natural_sort(values)
            combo.addItems([str(v) for v in sorted_values])
        combo.setEditable(True)
        combo.setPlaceholderText("输入或选择可用的分类值")
        if column in self.initial_data:
            preset = str(self.initial_data[column])
            idx = combo.findText(preset)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setEditText(preset)
        return combo

    def _create_numeric_field(self, column: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setDecimals(4)
        stats = self.column_stats.get('numerical', {}).get(column, {})
        min_val = stats.get('min')
        max_val = stats.get('max')
        spin.setRange(-1e9, 1e9)
        span = (max_val - min_val) if (min_val is not None and max_val is not None) else 1.0
        span = abs(span) if span != 0 else 1.0
        spin.setSingleStep(max(span / 100.0, 0.01))
        if min_val is not None and max_val is not None:
            spin.setToolTip(f"建议范围: {min_val:.4f} ~ {max_val:.4f}")
        default = stats.get('default')
        if column in self.initial_data:
            default = float(self.initial_data[column])
        elif default is None:
            if min_val is not None and max_val is not None:
                default = (min_val + max_val) / 2
            else:
                default = 0.0
        spin.setValue(default)
        return spin

    def get_data(self) -> dict:
        data = {}
        for col, widget in self.categorical_inputs.items():
            data[col] = widget.currentText().strip()
        for col, widget in self.numeric_inputs.items():
            data[col] = float(widget.value())
        if self.target_col and self.normal_value and self.target_col not in data:
            data[self.target_col] = self.normal_value
        return data

