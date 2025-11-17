import importlib.util
import os
import shutil
import pickle
import pandas as pd
from contextlib import redirect_stdout
from PySide6.QtCore import QObject, Signal


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAYESIAN_ROOT = os.path.join(PROJECT_ROOT, "Bayesian_1130")
DATA_DIR = os.path.join(BAYESIAN_ROOT, "datas")
RESULT_DIR = os.path.join(BAYESIAN_ROOT, "result", "bayesian_results")
BINNING_CONFIG_PATH = os.path.join(BAYESIAN_ROOT, "Apriori", "分箱配置.json")
DEFAULT_MODEL_PATH = os.path.join(BAYESIAN_ROOT, "Bayesian", "models", "final_bn_model.pkl")

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

    def __init__(self, model_path, data):
        super().__init__()
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.data = data

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
        predict_status_module.MODEL_PATH = self.model_path
        predict_status_module.DATA_PATH = csv_path
        predict_status_module.BINNING_CONFIG_PATH = BINNING_CONFIG_PATH
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
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        self.progress_updated.emit(30)

        binning_config = predict_status_module.load_binning_config(BINNING_CONFIG_PATH)
        dataset_config = binning_config["metadata"]["dataset_config"]
        target_col = dataset_config["target_col"]
        single_input = dict(data_dict)
        if target_col not in single_input:
            single_input[target_col] = dataset_config.get("normal_value", "正常")

        df_single = pd.DataFrame([single_input])
        discrete = predict_status_module.discretize_raw_data_for_prediction(df_single, binning_config)
        self.progress_updated.emit(60)

        normal_value = dataset_config.get("normal_value") or \
            binning_config.get("data_info", {}).get("target_info", {}).get("normal_value")
        predictions, prediction_probs = predict_status_module.predict_with_model(
            model,
            discrete,
            target_col=target_col,
            normal_value=normal_value or "正常"
        )
        self.progress_updated.emit(100)

        prediction = predictions[0] if predictions else "未知"
        probs = prediction_probs[0] if prediction_probs else {}
        self.single_prediction_finished.emit(prediction, data_dict, probs)
