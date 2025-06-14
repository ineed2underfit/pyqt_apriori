from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from api.api import demo_api
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog
import os


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

class Page4Handler(QObject):
    def __init__(self, parent: 'Page4'):
        super().__init__(parent)
        # Handler 通过 parent 参数持有 View 引用
        self._parent = parent

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


