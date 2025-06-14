from PySide6.QtCore import QObject

from api.api import demo_api
from common.utils import show_dialog
from workers.TaskManager import task_manager
from PySide6.QtWidgets import QFileDialog
import os

class PageTwoHandler(QObject):
    def __init__(self, parent: 'PageTwo'):
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



    def handle_case_split(self):
        # 在这里处理你的案例分割逻辑，之后弹窗显示统计信息

        message = (
            "处理完成！\n"
            "新增名词短语数：3624，新增动词短语数：5948，新增语句数：1732\n"
            "更新后名词短语总数：3624，动词短语总数：5948，语句总数：1732\n"
            "短语库和语句库已更新！"
        )
        show_dialog(self._parent, message, "语料提取完成")