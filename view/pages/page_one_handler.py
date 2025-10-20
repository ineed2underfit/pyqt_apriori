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
        # 只转换前100行作为预览，避免UI卡顿
        display_text = df.head(10000).to_string() + f"\n\n... (文件共 {len(df)} 行, 仅显示前10000行作为预览)"
        
        # 将所有需要的数据一并返回
        return (file_path, file_name, file_size_mb, display_text)

    def _on_load_success(self, result):
        """文件加载成功后的回调函数"""
        self._parent.close_state_tooltip()
        
        file_path, file_name, file_size_mb, display_text = result

        # 更新UI
        self._parent.textEdit.setText(display_text)

        # 发出文件选择信号，通知MainWindow
        self._parent.emit_file_selected(file_path)

        # 显示成功弹窗
        message = f'已选择文件:\n文件名: {file_name}\n文件路径: {file_path}\n文件大小: {file_size_mb} MB'
        show_dialog(self._parent, message, '文件选择成功')

    def _on_load_error(self, error_message):
        """文件加载失败的回调"""
        self._parent.close_state_tooltip()
        self._parent.on_common_error(f'处理文件时出错: {error_message}')