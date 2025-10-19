from PySide6.QtCore import QObject
import pandas as pd
from api.api import demo_api
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog
import os

class PageOneHandler(QObject):
    def __init__(self, parent: 'PageOne'):
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
                "E:/pycharm_projects/pyqt/pyqt-fluent-widgets-template/pyqt_apriori/apriori",  # 默认路径设置为apriori文件夹
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
            # 将字节转换为MB，并保留2位小数
            file_size_mb = round(file_size / (1024 * 1024), 2)

            # 读取CSV文件并显示在textEdit中
            df = pd.read_csv(file_path, encoding='utf-8')
            display_text = df.to_string()
            self._parent.textEdit.setText(display_text)

            # 发出文件选择信号
            self._parent.emit_file_selected(file_path)

            # 显示文件信息弹窗
            message = f'已选择文件:\n文件名: {file_name}\n文件路径: {file_path}\n文件大小: {file_size_mb} MB'
            show_dialog(self._parent, message, '文件选择成功')


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

    def handle_case_split(self):
        # 在这里处理你的案例分割逻辑，之后弹窗显示统计信息

        message = (
            "处理完成！统计信息：\n"
            "原始案例库案例数量: 0\n"
            "新分割案例数量: 6\n"
            "重复案例数量: 0 (查重功能已关闭)\n"
            "最终案例库案例数量: 157"
        )
        show_dialog(self._parent, message, "案例分割完成")