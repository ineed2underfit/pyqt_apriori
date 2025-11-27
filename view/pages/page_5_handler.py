from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from api.api import demo_api
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog
import os
import pandas as pd


class ConfirmDialog(QDialog):
    """确认对话框类"""

    def __init__(self, parent=None, title="确认", message=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 120)
        self.setModal(True)  # 设置为模态对话框

        # 设置布局
        layout = QVBoxLayout()

        # 添加消息标签
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 创建接受和拒绝按钮
        self.accept_button = QPushButton("接受(y)")
        self.reject_button = QPushButton("拒绝(n)")

        # 设置按钮样式（可选，让它们看起来更好看）
        button_style = """
            QPushButton {
                padding: 4px 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                min-width: 8px;  /* 设置最小宽度 */
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        self.accept_button.setStyleSheet(button_style)
        self.reject_button.setStyleSheet(button_style)

        # 连接按钮信号
        self.accept_button.clicked.connect(self.accept)
        self.reject_button.clicked.connect(self.reject)

        # 添加按钮到布局
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.reject_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

class Page5Handler(QObject):
    def __init__(self, parent: 'Page5'):
        super().__init__(parent)
        # Handler 通过 parent 参数持有 View 引用
        self._parent = parent
        self._current_dataset_path = None
        self._cached_device_col = None
        self._cached_target_col = None
        self._cached_normal_value = None

    def update_device_options_from_path(self, dataset_path: str):
        """根据 Page4 导入的测试集刷新设备选项"""
        if not dataset_path or not os.path.exists(dataset_path):
            return
        try:
            df = pd.read_csv(dataset_path)
        except Exception as exc:
            show_dialog(self._parent, f'加载测试数据失败: {exc}', '错误')
            return

        device_col, target_col, normal_value = self._detect_columns(df)
        if not device_col:
            return

        self._populate_device_options(df, device_col)
        self._current_dataset_path = dataset_path



    def query_fault_records(self):
        """查询设备故障记录"""
        try:
            dataset_path = self._get_page4_dataset_path()
            if not dataset_path:
                return

            df = pd.read_csv(dataset_path)
            device_col, target_col, normal_value = self._detect_columns(df)
            if not device_col or not target_col:
                return

            if dataset_path != self._current_dataset_path:
                self._populate_device_options(df, device_col)
                self._current_dataset_path = dataset_path

            selected_device = self._parent.comboBox.currentText().strip()
            if not selected_device:
                show_dialog(self._parent, '请先选择设备型号', '提示')
                return

            fault_records = df[
                (df[device_col].astype(str) == selected_device) &
                (df[target_col] != normal_value)
            ]

            if 'timestamp' in fault_records.columns:
                fault_records = fault_records.sort_values('timestamp', ascending=False)

            if fault_records.empty:
                output_html = self._format_no_fault_message(selected_device)
                self._parent.textEdit.setHtml(output_html)
                return

            output_html = self._format_fault_records_table(
                selected_device,
                fault_records,
                target_col=target_col,
                normal_value=normal_value,
                device_col=device_col
            )
            self._parent.textEdit.setHtml(output_html)

        except Exception as e:
            show_dialog(self._parent, f'查询故障记录时出错: {str(e)}', '错误')
            import traceback
            traceback.print_exc()

    def _get_page4_dataset_path(self):
        """获取 Page4 已导入的测试集路径"""
        main_window = self._parent.window()
        page4 = getattr(main_window, 'page4', None)
        handler = getattr(page4, 'handler', None) if page4 else None
        dataset_path = getattr(handler, 'test_data_path', None) if handler else None

        if not dataset_path:
            show_dialog(self._parent, '请先在 Page4 导入测试数据并完成质量评估', '提示')
            return None

        if not os.path.exists(dataset_path):
            show_dialog(self._parent, '测试数据文件不存在，请重新导入', '错误')
            return None

        return dataset_path

    def _detect_columns(self, df):
        """结合配置与列名，识别设备列、目标列以及正常值"""
        main_window = self._parent.window()
        dataset_info = getattr(main_window, 'dataset_config_info', {}) or {}

        dataset_config = {}
        if isinstance(dataset_info, dict):
            dataset_config = dataset_info.get('dataset_config') or dataset_info
        if not isinstance(dataset_config, dict):
            dataset_config = {}

        target_candidates = []
        for key in ('target_col', 'target_column', 'target', 'target_field'):
            value = dataset_config.get(key)
            if value:
                target_candidates.append(value)

        target_col = next((c for c in target_candidates if c in df.columns), None)
        if not target_col:
            fallback_target = ['status', '故障类型', '目标列']
            target_col = next((c for c in fallback_target if c in df.columns), None)

        if not target_col:
            show_dialog(self._parent, '无法识别故障标签列，请检查数据配置', '错误')
            return None, None, None

        normal_value = (
            dataset_config.get('normal_value') or
            dataset_config.get('normal_label') or
            dataset_config.get('normal_state') or
            '正常运行'
        )

        categorical_cols = dataset_config.get('categorical_columns') or dataset_config.get('categorical_cols')
        if isinstance(categorical_cols, str):
            categorical_cols = [item.strip() for item in categorical_cols.split(',') if item.strip()]
        categorical_cols = categorical_cols or []

        id_cols = dataset_config.get('id_cols') or []
        if isinstance(id_cols, str):
            id_cols = [item.strip() for item in id_cols.split(',') if item.strip()]

        device_candidates = []
        for key in ('device_column', 'device_col', 'device_field'):
            value = dataset_config.get(key)
            if value:
                device_candidates.append(value)
        device_candidates.extend(id_cols)
        device_candidates.extend(categorical_cols)

        device_col = self._select_device_column(df, device_candidates)
        if not device_col:
            show_dialog(self._parent, '无法识别设备列，请检查数据配置', '错误')
            return None, None, None

        self._cached_device_col = device_col
        self._cached_target_col = target_col
        self._cached_normal_value = normal_value
        return device_col, target_col, normal_value

    def _populate_device_options(self, df, device_col):
        """按照自然排序刷新下拉框"""
        values = (
            df[device_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        values = sorted(values, key=self._natural_sort_key)

        self._parent.comboBox.blockSignals(True)
        self._parent.comboBox.clear()
        self._parent.comboBox.addItems(values)
        self._parent.comboBox.blockSignals(False)

    def _natural_sort_key(self, value: str):
        import re

        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        return [convert(c) for c in re.split(r'(\d+)', value)]

    def _select_device_column(self, df, preferred_candidates):
        """根据优先级挑选设备列，优先使用“设备名称”或“device_id”"""
        priority = []
        for name in ("设备名称", "device_name", "device_id", "dev_id", "设备编号"):
            if name not in priority:
                priority.append(name)
        for candidate in preferred_candidates or []:
            if candidate and candidate not in priority:
                priority.append(candidate)
        for fallback in ("设备型号", "device_code"):
            if fallback not in priority:
                priority.append(fallback)

        for column in priority:
            if column in df.columns:
                return column
        return None

    def _format_no_fault_message(self, device_id):
        """格式化无故障记录的展示信息"""
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif; padding: 20px;">'
        html += '<div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 30px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        html += '<div style="font-size: 40pt; margin-bottom: 15px;">✔</div>'
        html += '<h3 style="margin: 0 0 10px 0; color: #27ae60; font-size: 12pt;">设备运行正常</h3>'
        html += f'<p style="margin: 0; color: #34495e; font-size: 10pt;">设备 <strong>{device_id}</strong> 暂无异常记录</p>'
        html += '<p style="margin: 10px 0 0 0; color: #7f8c8d; font-size: 9pt;">所有监测项均处于安全范围</p>'
        html += '</div>'
        html += '</div>'
        return html

    def _format_fault_records_table(self, device_id, fault_records, target_col, normal_value, device_col):
        """格式化故障记录为 HTML 表格"""
        record_count = len(fault_records)
        fault_type_counts = fault_records[target_col].value_counts()

        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'
        html += '<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); border-radius: 6px;">'
        html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10pt;">⚠ 故障类型分布</h3>'
        html += '<ul style="margin: 5px 0; padding-left: 25px; color: #34495e;">'
        for fault_type, count in fault_type_counts.items():
            percentage = (count / record_count) * 100
            html += f'<li style="margin: 3px 0;"><strong>{fault_type}</strong>: {count} 条 ({percentage:.1f}%)</li>'
        html += '</ul>'
        html += '</div>'

        html += '<h3 style="margin: 15px 0 10px 0; color: #2c3e50; font-size: 10pt;">📋 详细故障记录</h3>'

        display_columns = []
        optional_columns = ['timestamp', device_col, 'department', 'temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', target_col]
        for col in optional_columns:
            if col in fault_records.columns and col not in display_columns:
                display_columns.append(col)

        column_names = {
            'timestamp': '时间',
            'device_id': '设备ID',
            'department': '部门',
            'temp': '温度(°C)',
            'vibration': '振动',
            'oil_pressure': '油压',
            'voltage': '电压(V)',
            'rpm': '转速(RPM)',
        }
        column_names[device_col] = column_names.get(device_col, device_col)
        column_names[target_col] = column_names.get(target_col, target_col)

        html += '<div style="background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<thead style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #2c3e50;">'
        html += '<tr>'
        for col in display_columns:
            name = column_names.get(col, col)
            html += f'<th style="padding: 10px 8px; text-align: left; font-weight: bold; font-size: 9pt;">{name}</th>'
        html += '</tr>'
        html += '</thead>'

        html += '<tbody>'
        for idx, (_, row) in enumerate(fault_records.iterrows()):
            row_style = 'background-color: #f8f9fa;' if idx % 2 == 0 else 'background-color: white;'
            html += f'<tr style="{row_style}">'
            for col in display_columns:
                value = row[col]
                if col in {'temp', 'vibration', 'oil_pressure', 'voltage', 'rpm'}:
                    try:
                        value = f'{float(value):.2f}'
                    except Exception:
                        pass

                if col == target_col:
                    html += f'<td style="padding: 10px 8px; font-weight: bold; color: #e74c3c;">{value}</td>'
                else:
                    html += f'<td style="padding: 10px 8px; color: #2c3e50;">{value}</td>'
            html += '</tr>'
        html += '</tbody>'
        html += '</table>'
        html += '</div>'

        html += '<p style="margin-top: 10px; color: #7f8c8d; font-size: 9pt;">'
        html += f'共 {record_count} 条记录，展示设备 <strong>{device_id}</strong> 的异常历史（标准状态：{normal_value}）。'
        html += '</p>'
        html += '</div>'
        return html

    def do_something(self):
        pass
        show_dialog(self._parent, 'do something')

    def do_something_async(self):
        self._parent.show_state_tooltip('正在加载', '请稍后...')
        try:
            task_manager.submit_task(
                demo_api.sleep, args=(2,),
                on_success=self.on_do_something_async_success,
                on_error=lambda msg: self._parent.on_common_error(msg)
            )
        except RuntimeError as e:
            self._parent.close_state_tooltip()
            self._parent.on_common_error(str(e))

    def on_do_something_async_success(self, result):
        self._parent.close_state_tooltip()
        show_dialog(self._parent, 'do something async success')

    def select_file(self):
        """选择文件的方法"""
        try:
            # 打开文件选择对话框
            file_path, file_type = QFileDialog.getOpenFileName(
                self._parent,  # 父窗口
                "选择数据文件",  # 对话框标题
                "",  # 默认路径（空字符串表示当前目录）
                "所有支持的文件 (*.txt *.csv *.xlsx *.json);;文本文件 (*.txt);;CSV文件 (*.csv);;Excel文件 (*.xlsx);;JSON文件 (*.json);;所有文件 (*.*)"
                # 文件类型过滤器
            )

            # 如果用户选择了文件（没有取消）
            if file_path:
                self.handle_selected_file(file_path)
            else:
                show_dialog(self._parent, '未选择任何文件', '提示')

        except Exception as e:
            show_dialog(self._parent, f'文件选择出错: {str(e)}', '错误')

    def handle_selected_file(self, file_path):
        """处理选中的文件"""
        try:
            # 获取文件信息
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 这里可以根据你的需求处理文件
            # 例如：读取文件内容、验证文件格式、显示文件信息等

            message = f'已选择文件:\n文件名: {file_name}\n文件路径: {file_path}\n文件大小: {file_size} 字节'
            show_dialog(self._parent, message, '文件选择成功')

            # 如果需要异步处理文件，可以这样做：
            # self.process_file_async(file_path)

        except Exception as e:
            show_dialog(self._parent, f'处理文件时出错: {str(e)}', '错误')

    def process_file_async(self, file_path):
        """异步处理文件的方法（如果需要的话）"""
        self._parent.show_state_tooltip('正在处理文件', '请稍后...')
        try:
            task_manager.submit_task(
                self.read_file_content, args=(file_path,),
                on_success=self.on_file_process_success,
                on_error=lambda msg: self._parent.on_common_error(msg)
            )
        except RuntimeError as e:
            self._parent.close_state_tooltip()
            self._parent.on_common_error(str(e))

    def read_file_content(self, file_path):
        """读取文件内容（在后台线程中执行）"""
        # 这里添加你的文件读取逻辑
        # 例如读取 CSV、Excel、JSON 等
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def on_file_process_success(self, result):
        """文件处理成功的回调"""
        self._parent.close_state_tooltip()
        show_dialog(self._parent, '文件处理完成', '成功')

    def show_case_lib_popout(self):
        # 在这里处理你的案例分割逻辑，之后弹窗显示统计信息

        message = (
            " 案例1 已添加到案例库\n"
            "最终案例库案例数量: 158"
        )
        show_dialog(self._parent, message, "添加成功")

    def show_question_lib_confirm_dialog(self):
        """显示确认对话框，询问是否将案例添加到问题库"""
        confirm_dialog = ConfirmDialog(
            parent=self._parent,
            title="确认操作",
            message="是否将 案例1 添加到问题库? (y/n)"
        )

        # 显示对话框并获取结果
        result = confirm_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # 用户点击了接受按钮，执行添加到问题库的操作
            self.show_question_lib_popout()
        # 如果用户点击拒绝按钮或关闭对话框，什么都不做，对话框会自动关闭

    def show_question_lib_popout(self):
        # 在这里处理你的案例分割逻辑，之后弹窗显示统计信息

        # 使用项目相对路径保存案例
        # page_5_handler.py -> pages -> view -> 项目根目录 (向上2级)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        case_dir = os.path.join(project_root, "data", "problem_library")
        os.makedirs(case_dir, exist_ok=True)
        case_path = os.path.join(case_dir, "case_1.txt")
        
        message = (
            f" 案例1 已保存到：{case_path}\n"
            "案例1 已添加到问题库"
        )
        show_dialog(self._parent, message, "添加成功")

    # def handle_reject_button_click(self):
    #     """处理拒绝按钮点击事件，弹出确认对话框"""
    #     # 创建消息框
    #     msg_box = QMessageBox(self._parent)
    #     msg_box.setWindowTitle("确认操作")
    #     msg_box.setText("是否将 案例1 添加到问题库?")
    #     msg_box.setIcon(QMessageBox.Icon.Question)
    #
    #     # 添加自定义按钮
    #     accept_button = msg_box.addButton("接受", QMessageBox.ButtonRole.AcceptRole)
    #     reject_button = msg_box.addButton("拒绝", QMessageBox.ButtonRole.RejectRole)
    #
    #     # 显示对话框并获取用户选择
    #     msg_box.exec()
    #
    #     # 根据用户点击的按钮执行相应操作
    #     if msg_box.clickedButton() == accept_button:
    #         # 用户点击了接受按钮，执行 show_question_lib_popout 函数
    #         self.show_question_lib_popout()
    #     elif msg_box.clickedButton() == reject_button:
    #         # 用户点击了拒绝按钮，直接关闭对话框（什么都不做）
    #         pass
