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

    def query_fault_records(self):
        """查询设备故障记录"""
        try:
            # 1. 获取选择的设备ID
            selected_device = self._parent.comboBox.currentText()
            
            if not selected_device:
                show_dialog(self._parent, '请先选择设备型号', '提示')
                return
            
            # 2. 获取数据集路径（从 MainWindow）
            main_window = self._parent.window()
            dataset_path = main_window.dataset_path
            
            if not dataset_path or not os.path.exists(dataset_path):
                show_dialog(self._parent, '数据集未导入或文件不存在，请先在 Page 1 中导入数据集。', '错误')
                return
            
            # 3. 读取数据集
            df = pd.read_csv(dataset_path)
            
            # 4. 检查必要的列是否存在
            required_columns = ['device_id', '故障类型']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                show_dialog(self._parent, f'数据集缺少必要的列: {", ".join(missing_columns)}', '错误')
                return
            
            # 5. 筛选数据：设备ID匹配 且 故障类型不是"正常运行"
            fault_records = df[
                (df['device_id'] == selected_device) & 
                (df['故障类型'] != '正常运行')
            ]
            
            # 6. 按时间排序（如果有 timestamp 列）
            if 'timestamp' in fault_records.columns:
                fault_records = fault_records.sort_values('timestamp', ascending=False)
            
            # 7. 检查是否有故障记录
            if fault_records.empty:
                output_html = self._format_no_fault_message(selected_device)
                self._parent.textEdit.setHtml(output_html)
                return
            
            # 8. 格式化输出
            output_html = self._format_fault_records_table(selected_device, fault_records)
            
            # 9. 显示结果
            self._parent.textEdit.setHtml(output_html)
            
        except Exception as e:
            show_dialog(self._parent, f'查询故障记录时出错: {str(e)}', '错误')
            import traceback
            traceback.print_exc()
    
    def _format_no_fault_message(self, device_id):
        """格式化无故障记录的消息"""
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif; padding: 20px;">'        
        
        # 无故障提示
        html += '<div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 30px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'        
        html += '<div style="font-size: 48pt; margin-bottom: 15px;">✅</div>'
        html += f'<h3 style="margin: 0 0 10px 0; color: #27ae60; font-size: 12pt;">设备运行正常</h3>'
        html += f'<p style="margin: 0; color: #34495e; font-size: 10pt;">设备 <strong>{device_id}</strong> 没有故障记录</p>'
        html += '<p style="margin: 10px 0 0 0; color: #7f8c8d; font-size: 9pt;">所有记录均为正常运行状态</p>'
        html += '</div>'
        
        html += '</div>'
        return html
    
    def _format_fault_records_table(self, device_id, fault_records):
        """格式化故障记录为表格形式的 HTML（参考 Page 2 样式）"""
        record_count = len(fault_records)
        
        # 统计故障类型分布
        fault_type_counts = fault_records['故障类型'].value_counts()
        
        # 开始构建 HTML（参考 Page 2 的样式）
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'
        
        # 统计信息（参考 Page 2 的渐变背景）
        html += '<div style="margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); border-radius: 6px;">'        
        html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10pt;">📊 故障类型分布</h3>'
        html += '<ul style="margin: 5px 0; padding-left: 25px; color: #34495e;">'        
        for fault_type, count in fault_type_counts.items():
            percentage = (count / record_count) * 100
            html += f'<li style="margin: 3px 0;"><strong>{fault_type}</strong>: {count} 条 ({percentage:.1f}%)</li>'
        html += '</ul>'
        html += '</div>'
        
        # 详细记录表格（参考 Page 2 的表格样式）
        html += '<h3 style="margin: 15px 0 10px 0; color: #2c3e50; font-size: 10pt;">📝 详细故障记录</h3>'
        
        # 确定要显示的列
        display_columns = []
        optional_columns = ['timestamp', 'device_id', 'department', 'temp', 'vibration', 'oil_pressure', 'voltage', 'rpm', '故障类型']
        for col in optional_columns:
            if col in fault_records.columns:
                display_columns.append(col)
        
        # 中文列名映射
        column_names = {
            'timestamp': '时间',
            'device_id': '设备ID',
            'department': '部门',
            'temp': '温度(°C)',
            'vibration': '振动',
            'oil_pressure': '油压',
            'voltage': '电压(V)',
            'rpm': '转速(RPM)',
            '故障类型': '故障类型'
        }
        
        # 创建表格（参考 Page 2 的表格样式）
        html += '<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'        
        
        # 表头（参考 Page 2 的渐变背景）
        html += '<thead style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #2c3e50;">'        
        html += '<tr>'
        for col in display_columns:
            display_name = column_names.get(col, col)
            html += f'<th style="padding: 10px 8px; text-align: left; font-weight: bold; font-size: 9pt;">{display_name}</th>'
        html += '</tr>'
        html += '</thead>'
        
        # 表格内容
        html += '<tbody>'
        for idx, (_, row) in enumerate(fault_records.iterrows()):
            # 交替行颜色（参考 Page 2）
            row_style = "background-color: #f8f9fa;" if idx % 2 == 0 else "background-color: white;"
            html += f'<tr style="{row_style}">'            
            
            for col in display_columns:
                value = row[col]
                
                # 格式化数值
                if col in ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']:
                    try:
                        value = f'{float(value):.2f}'
                    except:
                        pass
                
                # 故障类型高亮显示
                if col == '故障类型':
                    # 根据故障类型选择颜色
                    if '散热' in str(value):
                        color = '#e74c3c'  # 红色
                    elif '传动' in str(value):
                        color = '#f39c12'  # 橙色
                    elif '润滑' in str(value):
                        color = '#3498db'  # 蓝色
                    elif '电力' in str(value):
                        color = '#9b59b6'  # 紫色
                    else:
                        color = '#34495e'
                    html += f'<td style="padding: 10px 8px; font-weight: bold; color: {color};">{value}</td>'
                else:
                    html += f'<td style="padding: 10px 8px; color: #2c3e50;">{value}</td>'
            
            html += '</tr>'
        
        html += '</tbody>'
        html += '</table>'
        
        html += '</div>'
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

        message = (
            " 案例1 已保存到：E:\PycharmProjects\oygq_new\deepseek\data\problem_library\case_1.txt\n"
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


