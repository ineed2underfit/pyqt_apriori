import importlib.util
import io
import os
import copy
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal

from common.utils import resolve_bayesian_path

APRIORI_MODULE_PATH = resolve_bayesian_path("Apriori", "Apriori.py")

_spec = importlib.util.spec_from_file_location("bayesian_equipment_analyzer", APRIORI_MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"无法加载 Apriori 模块: {APRIORI_MODULE_PATH}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
EquipmentAnalyzer = _module.EquipmentAnalyzer


@dataclass
class DatasetSelection:
    """保存用户在弹窗中选择的数据集配置"""

    target_col: str
    normal_value: str
    numerical_cols: List[str]
    categorical_cols: List[str]
    rule_pattern: str = "prediction"
    all_columns: List[str] = field(default_factory=list)


class AprioriService(QObject):
    """封装 Bayesian_1130/Apriori/Apriori.py 以供界面层调用"""

    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self._analyzer: Optional[EquipmentAnalyzer] = None
        self._dataset_path: Optional[str] = None
        self._current_selection: Optional[DatasetSelection] = None
        self._current_config: Optional[Dict] = None
        self._raw_dataframe = None
        self._cleaned_dataframe = None

    @property
    def dataset_path(self) -> Optional[str]:
        return self._dataset_path

    @property
    def current_selection(self) -> Optional[DatasetSelection]:
        return self._current_selection

    @property
    def raw_dataframe(self):
        return self._raw_dataframe

    @property
    def cleaned_dataframe(self):
        return self._cleaned_dataframe

    def get_dataset_config(self):
        if self._current_config is None:
            return None
        return copy.deepcopy(self._current_config)

    def get_rule_config(self):
        if not self._analyzer or not hasattr(self._analyzer, 'rule_config'):
            return None
        return copy.deepcopy(self._analyzer.rule_config)

    def configure_dataset(self, dataset_path: str, selection: DatasetSelection):
        """
        根据界面选择构建 EquipmentAnalyzer，并加载数据集

        Args:
            dataset_path: CSV 文件路径
            selection: 用户选择的列信息
        Returns:
            pandas.DataFrame: 读取后的原始数据（去重/编码处理前）
        """
        if not selection.all_columns:
            raise ValueError("缺少列清单，无法构建数据集配置")

        self._ensure_analyzer(dataset_path)
        dataset_config = self._build_dataset_config(selection)

        self._analyzer.set_dataset_config(dataset_config)
        rule_kwargs = self._build_rule_kwargs(selection.rule_pattern)
        self._analyzer.set_rule_config(**rule_kwargs)

        dataframe = self._analyzer.load_data(auto_detect=False, interactive=False)

        # 缓存状态，方便第2页直接引用
        self._current_selection = selection
        self._current_config = dataset_config
        self._raw_dataframe = dataframe
        self._cleaned_dataframe = None
        self._analyzer.raw_data = dataframe

        return dataframe

    def _ensure_analyzer(self, dataset_path: str):
        """懒加载 EquipmentAnalyzer 实例"""
        if self._analyzer is None or dataset_path != self._dataset_path:
            self._analyzer = EquipmentAnalyzer(file_path=dataset_path)
            self._dataset_path = dataset_path

    def _build_dataset_config(self, selection: DatasetSelection) -> Dict:
        """根据选择生成 EquipmentAnalyzer 所需的配置字典"""
        exclude = set(selection.numerical_cols + selection.categorical_cols + [selection.target_col])
        inferred_id_cols = [col for col in selection.all_columns if col not in exclude]
        feature_names = {col: col for col in selection.numerical_cols}

        config = {
            "numerical_cols": selection.numerical_cols,
            "categorical_cols": selection.categorical_cols,
            "target_col": selection.target_col,
            "id_cols": inferred_id_cols,
            "normal_value": selection.normal_value,
            "col_mapping": {},
            "feature_names": feature_names,
        }
        return config

    def _build_rule_kwargs(self, pattern: str) -> Dict:
        """根据选择的规则模式设置 Apriori 规则相关参数"""
        if pattern == "prediction":
            return {
                "rule_pattern": "prediction",
                "target_in_consequent": True,
                "target_in_antecedent": False,
                "custom_filter": None,
                "strict_target_consequent": True,
            }
        if pattern == "association":
            return {
                "rule_pattern": "association",
                "target_in_consequent": False,
                "target_in_antecedent": True,
                "custom_filter": None,
                "strict_target_consequent": False,
            }
        return {
            "rule_pattern": "custom",
            "target_in_consequent": True,
            "target_in_antecedent": True,
            "custom_filter": None,
            "strict_target_consequent": False,
        }

    def clean_data(self):
        """
        执行 Apriori 的数据清洗流程，返回清洗后的数据、报告以及日志文本
        """
        if not self._analyzer or self._raw_dataframe is None:
            raise ValueError("请先完成数据集配置并加载数据")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            cleaned_df = self._analyzer.clean_data(self._raw_dataframe.copy())
            self._analyzer.print_cleaning_report()

        log_text = buffer.getvalue()
        self._cleaned_dataframe = cleaned_df
        report = getattr(self._analyzer, "cleaning_report", {})
        self._analyzer.processed_data = cleaned_df
        return cleaned_df, report, log_text
