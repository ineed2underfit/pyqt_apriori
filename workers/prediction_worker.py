import importlib.util
import os
import shutil
from contextlib import redirect_stdout
from PySide6.QtCore import QObject, Signal

from common.utils import get_bayesian_root

BAYESIAN_ROOT = get_bayesian_root()
DATA_DIR = str(BAYESIAN_ROOT / "datas")
APRIORI_RESULT_DIR = BAYESIAN_ROOT / "result" / "apriori_results"
COMPREHENSIVE_CONFIG_PATH = str(APRIORI_RESULT_DIR / "完整数据配置.json")
BASIC_BINNING_PATH = str(APRIORI_RESULT_DIR / "分箱配置.json")
RESULT_DIR = str(BAYESIAN_ROOT / "result" / "bayesian_results")
DEFAULT_MODEL_PATH = str(BAYESIAN_ROOT / "Bayesian" / "models" / "final_bn_model.pkl")
RULES_CSV_PATH = str(APRIORI_RESULT_DIR / "关联规则分析结果.csv")
RULES_JSON_PATH = str(BAYESIAN_ROOT / "result" / "bayesian_results" / "network_rules_with_mapping.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


def _load_module(module_name, relative_path):
    module_path = os.path.join(BAYESIAN_ROOT, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


predict_status_module = _load_module(
    "bayesian_predict_status",
    os.path.join("Bayesian", "predict_status.py")
)


def _resolve_binning_config_path():
    if os.path.exists(COMPREHENSIVE_CONFIG_PATH):
        return COMPREHENSIVE_CONFIG_PATH
    if os.path.exists(BASIC_BINNING_PATH):
        return BASIC_BINNING_PATH
    raise FileNotFoundError(
        "未找到完整数据配置文件，请先在页面二完成规则挖掘: "
        f"{COMPREHENSIVE_CONFIG_PATH}"
    )


class LogEmitter:
    def __init__(self, signal):
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


class PredictionWorker(QObject):
    batch_finished = Signal(str, str)  # report_text, confusion_matrix_path
    single_prediction_finished = Signal(str, object, object)
    error = Signal(str)
    progress_updated = Signal(int)
    log_message = Signal(str)

    def __init__(self, model_path, data, history_data_path=None):
        super().__init__()
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.data = data
        self.history_data_path = history_data_path

    def run(self):
        try:
            if isinstance(self.data, str):
                csv_path = self._prepare_csv(self.data)
                self._run_batch(csv_path)
            elif isinstance(self.data, dict):
                self._run_single(self.data)
            else:
                raise ValueError("不支持的数据类型")
        except Exception as exc:
            self.error.emit(str(exc))

    def _prepare_csv(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"测试数据不存在: {file_path}")
        target_path = os.path.join(DATA_DIR, os.path.basename(file_path))
        if os.path.abspath(file_path) != os.path.abspath(target_path):
            shutil.copy2(file_path, target_path)
        return target_path

    def _run_batch(self, csv_path):
        self.progress_updated.emit(10)
        binning_config_path = _resolve_binning_config_path()
        predict_status_module.MODEL_PATH = self.model_path
        predict_status_module.DATA_PATH = csv_path
        predict_status_module.BINNING_CONFIG_PATH = binning_config_path
        predict_status_module.RESULT_DIR = RESULT_DIR

        emitter = LogEmitter(self.log_message)
        with redirect_stdout(emitter):
            predict_status_module.main()

        report_file = os.path.join(RESULT_DIR, "prediction_report.txt")
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                report_text = f.read()
        else:
            report_text = "预测完成，但未找到 prediction_report.txt"
        cm_path = os.path.join(RESULT_DIR, "confusion_matrix.png")
        if not os.path.exists(cm_path):
            cm_path = ""

        self.progress_updated.emit(100)
        self.batch_finished.emit(report_text, cm_path)

    def _run_single(self, data_dict):
        self.progress_updated.emit(10)
        binning_config_path = _resolve_binning_config_path()
        if not self.history_data_path:
            raise FileNotFoundError("请先在 Page1 导入并配置数据集")
        if not os.path.exists(self.history_data_path):
            raise FileNotFoundError(f"历史数据集不存在: {self.history_data_path}")

        predict_status_module.MODEL_PATH = self.model_path
        predict_status_module.BINNING_CONFIG_PATH = binning_config_path
        predict_status_module.RULES_JSON_PATH = RULES_JSON_PATH
        predict_status_module.RULES_CSV_PATH = RULES_CSV_PATH
        predict_status_module.RESULT_DIR = RESULT_DIR

        single_input = dict(data_dict)
        status, prob_dict = predict_status_module.run_single_assessment(
            single_input,
            history_data_path=self.history_data_path,
            model_path=self.model_path,
            binning_config_path=binning_config_path,
            rules_json_path=RULES_JSON_PATH,
            rules_csv_path=RULES_CSV_PATH,
            result_dir=RESULT_DIR
        )
        self.progress_updated.emit(100)
        self.single_prediction_finished.emit(status, data_dict, prob_dict)
