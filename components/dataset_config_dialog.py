from typing import List, Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from common.utils import show_dialog
from services.apriori_service import DatasetSelection


class DatasetConfigDialog(QDialog):
    """在 GUI 中替代 CLI 交互的列配置弹窗"""

    def __init__(self, dataframe: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据列配置")
        self.resize(720, 520)

        self._dataframe = dataframe
        self._columns: List[str] = dataframe.columns.tolist()
        self._result: Optional[DatasetSelection] = None

        self._build_ui()
        self._populate_columns()
        self._on_target_changed()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "请选择目标列、正常值以及需要参与 Apriori 分析的字段，"
            "该弹窗替代命令行中的交互式配置。"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        layout.addLayout(form)

        self.targetCombo = QComboBox()
        form.addRow("目标列", self.targetCombo)

        self.normalValueCombo = QComboBox()
        self.normalValueCombo.setEditable(True)
        form.addRow("正常值标识", self.normalValueCombo)

        self.ruleModeCombo = QComboBox()
        self.ruleModeCombo.addItem("1. prediction（预测模式）", "prediction")
        self.ruleModeCombo.addItem("2. association（关联模式）", "association")
        self.ruleModeCombo.addItem("3. custom（自定义模式）", "custom")
        self.ruleModeCombo.setCurrentIndex(0)
        form.addRow("规则模式", self.ruleModeCombo)

        list_layout = QHBoxLayout()
        layout.addLayout(list_layout)

        self.numericalList = QListWidget()
        self.numericalList.setSelectionMode(QAbstractItemView.MultiSelection)
        list_layout.addWidget(self._wrap_with_label("数值列（连续特征）", self.numericalList))

        self.categoricalList = QListWidget()
        self.categoricalList.setSelectionMode(QAbstractItemView.MultiSelection)
        list_layout.addWidget(self._wrap_with_label("分类列（离散特征）", self.categoricalList))

        self.targetCombo.currentIndexChanged.connect(self._on_target_changed)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def _wrap_with_label(self, title: str, widget: QListWidget):
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        label = QLabel(title)
        label.setAlignment(Qt.AlignLeft)
        container_layout.addWidget(label)
        container_layout.addWidget(widget)
        return container_widget

    def _populate_columns(self):
        self.targetCombo.clear()
        self.numericalList.clear()
        self.categoricalList.clear()

        for idx, column in enumerate(self._columns, start=1):
            dtype = str(self._dataframe[column].dtype)
            display_text = f"{idx}. {column} ({dtype})"
            self.targetCombo.addItem(display_text, column)

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, column)
            self.numericalList.addItem(item)
            if pd.api.types.is_numeric_dtype(self._dataframe[column]):
                item.setSelected(True)

            cat_item = QListWidgetItem(display_text)
            cat_item.setData(Qt.UserRole, column)
            self.categoricalList.addItem(cat_item)
            if pd.api.types.is_object_dtype(self._dataframe[column]):
                cat_item.setSelected(True)

    def _on_target_changed(self):
        self._populate_normal_values()
        self._sync_target_state()

    def _populate_normal_values(self):
        column = self.targetCombo.currentData()
        self.normalValueCombo.clear()
        if not column or column not in self._dataframe.columns:
            return

        series = self._dataframe[column].dropna().astype(str)
        value_counts = series.value_counts().head(20).index.tolist()
        if value_counts:
            self.normalValueCombo.addItems(value_counts)
            self.normalValueCombo.setCurrentIndex(0)
        else:
            self.normalValueCombo.setEditText("")

    def _sync_target_state(self):
        current_target = self.targetCombo.currentData()
        for widget in (self.numericalList, self.categoricalList):
            for index in range(widget.count()):
                item = widget.item(index)
                is_target = item.data(Qt.UserRole) == current_target
                flags = item.flags()
                if is_target:
                    item.setSelected(False)
                    item.setFlags(flags & ~Qt.ItemIsEnabled)
                else:
                    item.setFlags(flags | Qt.ItemIsEnabled)

    def get_result(self) -> Optional[DatasetSelection]:
        return self._result

    def accept(self):
        selection = self._collect_selection()
        if not selection:
            return
        self._result = selection
        super().accept()

    def _collect_selection(self) -> Optional[DatasetSelection]:
        target_col = self.targetCombo.currentData()
        if not target_col:
            show_dialog(self, "请选择目标列", "提示")
            return None

        normal_value = self.normalValueCombo.currentText().strip()
        if not normal_value:
            show_dialog(self, "正常值标识不能为空", "提示")
            return None

        numerical_cols = self._selected_columns(self.numericalList)
        categorical_cols = self._selected_columns(self.categoricalList)

        if target_col in numerical_cols:
            numerical_cols.remove(target_col)
        if target_col in categorical_cols:
            categorical_cols.remove(target_col)

        if not numerical_cols and not categorical_cols:
            show_dialog(self, "至少选择一列作为分析特征", "提示")
            return None

        selection = DatasetSelection(
            target_col=target_col,
            normal_value=normal_value,
            numerical_cols=numerical_cols,
            categorical_cols=categorical_cols,
            rule_pattern=self.ruleModeCombo.currentData(),
            all_columns=self._columns.copy(),
        )
        return selection

    @staticmethod
    def _selected_columns(widget: QListWidget) -> List[str]:
        return [item.data(Qt.UserRole) for item in widget.selectedItems()]
