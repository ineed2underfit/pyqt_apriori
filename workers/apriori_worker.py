import importlib.util
import io
import os
import types
from contextlib import redirect_stdout

from PySide6.QtCore import QObject, Signal

from common.utils import resolve_bayesian_path

APRIORI_MODULE_PATH = resolve_bayesian_path("Apriori", "Apriori.py")
_spec = importlib.util.spec_from_file_location("gui_equipment_analyzer_worker", APRIORI_MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"无法加载 Apriori 模块: {APRIORI_MODULE_PATH}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
EquipmentAnalyzer = _module.EquipmentAnalyzer


class LogEmitter(io.TextIOBase):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self._buffer = ""

    def write(self, s):
        if not s:
            return 0
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self.signal.emit(line.rstrip())
        return len(s)

    def flush(self):
        if self._buffer.strip():
            self.signal.emit(self._buffer.strip())
        self._buffer = ""


class AprioriWorker(QObject):
    """后台执行 Apriori 关联规则挖掘"""

    log_message = Signal(str)
    progress_updated = Signal(int, str)
    analysis_succeeded = Signal(object)
    analysis_failed = Signal(str)

    def __init__(self, dataset_path, params, dataset_config=None, rule_config=None, data_frame=None, data_is_cleaned=False):
        super().__init__()
        self.dataset_path = dataset_path
        self.params = params or {}
        self.dataset_config = dataset_config
        self.rule_config = rule_config
        self.data_frame = data_frame
        self.data_is_cleaned = data_is_cleaned
        self.analyzer = None
        self._is_running = True

    def run(self):
        if not self._is_running:
            return

        try:
            self.progress_updated.emit(5, "准备执行规则挖掘...")

            params = dict(self.params)
            num_bins_from_params = params.pop('num_bins', 5)  # Default to 5 if not provided

            self.analyzer = EquipmentAnalyzer(
                file_path=self.dataset_path,
                num_bins=num_bins_from_params
            )

            if self.dataset_config:
                self.analyzer.set_dataset_config(self.dataset_config)
            if self.rule_config:
                self.analyzer.set_rule_config(**self.rule_config)

            if self.data_frame is not None:
                raw_df = self.data_frame
            else:
                raw_df = self.analyzer.load_data(auto_detect=False, interactive=False)
            self.analyzer.raw_data = raw_df
            self.progress_updated.emit(15, "数据加载完成，准备离散化优化...")

            def _cached_load_data(self_analyzer, auto_detect=True, interactive=False):
                return raw_df

            self.analyzer.load_data = types.MethodType(_cached_load_data, self.analyzer)
            if self.data_is_cleaned:
                def _no_clean(self_analyzer, df):
                    return df
                self.analyzer.clean_data = types.MethodType(_no_clean, self.analyzer)
                self.analyzer.print_cleaning_report = types.MethodType(lambda *_: None, self.analyzer)

            emitter = LogEmitter(self.log_message)
            self.progress_updated.emit(30, "开始离散化方法优化...")

            with redirect_stdout(emitter):
                results_df = self.analyzer.analyze(**params, interactive=False)

            emitter.flush()

            if not self._is_running:
                return

            if results_df is None or results_df.empty:
                self.analysis_failed.emit("分析完成，但未找到任何规则")
            else:
                try:
                    result_dir = self.analyzer.get_result_dir()
                    os.makedirs(result_dir, exist_ok=True)

                    # 保存最新规则结果，供贝叶斯模块直接使用
                    csv_path = os.path.join(result_dir, "关联规则分析结果.csv")
                    results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

                    # 导出完整配置（含分箱信息）
                    raw_data = getattr(self.analyzer, "raw_data", None)
                    processed_data = getattr(self.analyzer, "processed_data", None)
                    self.analyzer.export_comprehensive_config(result_dir, raw_data, processed_data)
                except Exception as export_exc:
                    if self.log_message:
                        self.log_message.emit(f"⚠️ 导出规则/配置失败: {export_exc}")
                self.analysis_succeeded.emit(results_df)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.analysis_failed.emit(f"分析过程中发生严重错误: {str(e)}")

    def stop(self):
        self._is_running = False
