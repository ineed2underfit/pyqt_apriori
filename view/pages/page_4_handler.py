from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QFileDialog
from common.utils import show_dialog
from workers.prediction_worker import PredictionWorker
import os

class PageFourHandler(QObject):
    def __init__(self, parent: 'Page4'):
        super().__init__(parent)
        self._parent = parent
        self.test_data_path = None
        self.thread = None
        self.worker = None

    # --- 批量评估功能 ---
    def select_test_file(self):
        """打开文件对话框，让用户选择测试数据集"""
        try:
            project_root = os.getcwd()
            default_dir = os.path.join(project_root, "new_bayesian", "dataset", "testdata_info")
            file_path, _ = QFileDialog.getOpenFileName(
                self._parent, "选择测试数据文件", default_dir, "CSV Files (*.csv);;All Files (*.*)"
            )
            if file_path:
                self.test_data_path = file_path
                self._parent.textEdit_3.setText(f"已选择测试文件进行批量评估：\n{file_path}")
                self._parent.pushButton_assessment.setEnabled(True)
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
        """对UI界面上输入的数据进行单次评估"""
        print("--- assess_single_instance 方法被调用 ---") # DEBUG
        try:
            # 从UI收集数据并打包成字典
            data_dict = {
                'timestamp': self._parent.dateTimeEdit.dateTime().toString(Qt.DateFormat.ISODate),
                'device_id': self._parent.comboBox_model.currentText(),
                'department': self._parent.comboBox_apt.currentText(),
                'temp': self._parent.doubleSpinBox_temp.value(),
                'vibration': self._parent.doubleSpinBox_vibration.value(),
                'oil_pressure': self._parent.doubleSpinBox_oil.value(),
                'voltage': self._parent.doubleSpinBox_voltage.value(),
                'rpm': self._parent.doubleSpinBox_rpm.value()
            }
            print(f"--- 收集到的单次评估数据: {data_dict} ---") # DEBUG
            self._run_prediction(data_dict)
        except Exception as e:
            print(f"--- assess_single_instance 发生错误: {e} ---") # DEBUG
            show_dialog(self._parent, f'读取界面数据时出错: {str(e)}', '错误')

    # --- 公共的执行和回调逻辑 ---
    def _run_prediction(self, data_payload):
        """通用的预测执行函数，根据传入数据类型启动不同模式"""
        print("--- _run_prediction 方法被调用 ---") # DEBUG
        main_window = self._parent.window()
        model_path = main_window.model_pkl_path

        if not os.path.exists(model_path):
            show_dialog(self._parent, f"模型文件不存在，请先在Page3中构建贝叶斯网络。\n路径: {model_path}", "错误")
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
            # 批量预测仍然显示弹窗
            show_dialog(self._parent, "正在进行批量预测...", "请稍候")

        self.thread = QThread()
        self.worker = PredictionWorker(model_path, data_payload)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.batch_finished.connect(self.on_batch_assessment_finished)
        self.worker.single_prediction_finished.connect(self.on_single_assessment_finished)
        self.worker.progress_updated.connect(self.on_progress_updated)  # 连接进度信号
        self.worker.error.connect(self.on_assessment_error)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_batch_assessment_finished(self, report_text):
        """批量评估成功的回调"""
        # 将纯文本报告包装为HTML，并尝试展示混淆矩阵图片
        # 约定混淆矩阵输出路径：new_bayesian/predict/results/confusion_matrix.png
        project_root = os.getcwd()
        cm_path = os.path.join(project_root, "new_bayesian", "predict", "results", "confusion_matrix.png")

        html = '<div style="font-size: 10pt; line-height: 1.6; color: #2c3e50;">'
        html += '<div style="padding: 10px 0; border-bottom: 2px solid #3498db; margin-bottom: 10px;">'
        html += '<span style="font-size: 12pt; font-weight: bold;">📋 批量质量评估报告</span>'
        html += '</div>'

        # 文本报告区域（左对齐、等宽字体更易读）
        html += '<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: Consolas, Menlo, monospace; font-size: 9pt; background: #f7f9fb; padding: 10px; border-radius: 6px; border: 1px solid #e3e9ef;">'
        html += self._escape_html(report_text)
        html += '</pre>'

        # 图片区域
        if os.path.exists(cm_path):
            html += '<div style="margin-top: 12px;">'
            html += '<div style="margin: 6px 0 8px 0; font-weight: bold; color: #34495e;">🧭 混淆矩阵</div>'
            # 注意：QTextEdit 支持本地图片相对/绝对路径
            html += f'<img src="{cm_path}" alt="confusion_matrix" style="max-width: 100%; border: 1px solid #e3e9ef; border-radius: 6px;" />'
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
        # 使用HTML格式化输出，字体稍大一点
        output = '<div style="font-size: 10pt; line-height: 1.6;">'
        output += '<p style="font-size: 11pt; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px;">⚡ 单次故障概率评估结果</p>'
        
        output += '<p style="font-size: 10.5pt; font-weight: bold; color: #34495e; margin-top: 12px;">📊 输入数据：</p>'
        output += '<table style="width: 100%; border-collapse: collapse; margin-top: 8px;">'
        
        # 中文映射
        field_names = {
            'timestamp': '⏰ 时间戳',
            'device_id': '🛠️ 设备ID',
            'department': '🏢 部门',
            'temp': '🌡️ 温度',
            'vibration': '📡 振动',
            'oil_pressure': '🛢️ 油压',
            'voltage': '⚡ 电压',
            'rpm': '♻️ 转速'
        }
        
        for key, value in input_data_dict.items():
            display_name = field_names.get(key, key)
            output += f'<tr style="border-bottom: 1px solid #ecf0f1;">'
            output += f'<td style="padding: 6px; font-weight: bold; color: #7f8c8d; width: 40%;">{display_name}</td>'
            output += f'<td style="padding: 6px; color: #2c3e50;">{value}</td>'
            output += '</tr>'
        
        output += '</table>'
        
        # 预测结果 - 根据结果类型选择颜色
        if prediction_result == "正常运行":
            # 正常运行用绿色
            result_color = "#27ae60"
            result_bg_color = "#d5f4e6"
            result_border_color = "#2ecc71"
            result_icon = "🟢"
        else:
            # 异常情况用红色
            result_color = "#e74c3c"
            result_bg_color = "#fef5e7"
            result_border_color = "#f39c12"
            result_icon = "🔴"
        
        # 检查最高概率是否低于阈值
        max_prob = max(probability_dist.values()) if probability_dist else 0
        confidence_threshold = 0.6
        
        if max_prob < confidence_threshold:
            # 低置信度提示
            output += f'<div style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; color: #856404;">'
            output += f'⚠️ <strong>低置信度警告</strong>：最高概率仅为 {max_prob:.1%}，预测结果可能不够可靠'
            output += '</div>'
        
        output += f'<p style="font-size: 12pt; font-weight: bold; color: {result_color}; margin-top: 15px; padding: 12px; background-color: {result_bg_color}; border-left: 5px solid {result_border_color}; border-radius: 5px;">{result_icon} 预测故障类型：<span style="color: {result_color}; font-size: 13pt;">{prediction_result}</span></p>'
        
        # 概率分布显示
        output += '<div style="margin-top: 15px;">'
        output += '<p style="font-size: 10.5pt; font-weight: bold; color: #34495e; margin-bottom: 8px;">📈 故障类型概率分布：</p>'
        output += '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #e9ecef;">'
        
        for i, (fault_type, prob) in enumerate(probability_dist.items()):
            # 根据概率大小选择颜色
            if prob > 0.5:
                bar_color = "#28a745"  # 绿色
            elif prob > 0.3:
                bar_color = "#ffc107"  # 黄色
            else:
                bar_color = "#dc3545"  # 红色
            
            # 概率条
            bar_width = prob * 100
            
            # 格式化概率显示：统一显示8位小数，不使用科学计数法
            prob_text = f'{prob * 100:.8f}%'
            
            output += f'<div style="margin-bottom: 6px;">'
            output += f'<div style="display: flex; align-items: center; margin-bottom: 3px;">'
            output += f'<span style="font-size: 9pt; color: #2c3e50; width: 120px; display: inline-block;">{fault_type}</span>'
            output += f'<span style="font-size: 9pt; color: #495057; margin-left: 8px; min-width: 80px;">{prob_text}</span>'
            output += f'</div>'
            output += f'<div style="background-color: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">'
            output += f'<div style="background-color: {bar_color}; height: 100%; width: {bar_width}%; transition: width 0.3s ease;"></div>'
            output += f'</div>'
            output += f'</div>'
        
        output += '</div>'
        output += '</div>'
        output += '</div>'

        self._parent.textEdit_solely.setHtml(output)
        self.cleanup_thread()
    def on_assessment_error(self, error_message):
        """评估失败的通用回调"""
        show_dialog(self._parent, f"评估失败: {error_message}", "错误")
        self.cleanup_thread()

    def cleanup_thread(self):
        """清理线程"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self._parent:
            self._parent.pushButton_import.setEnabled(True)
            # 只有在选择了测试文件后，才重新启用批量评估按钮
            if self.test_data_path:
                self._parent.pushButton_assessment.setEnabled(True)
            self._parent.pushButton_solely.setEnabled(True)
            # 隐藏进度条
            if hasattr(self._parent, 'progressBar'):
                self._parent.progressBar.setVisible(False)