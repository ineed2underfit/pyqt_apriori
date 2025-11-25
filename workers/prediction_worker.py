import importlib.util
import os
import shutil
import pickle
import pandas as pd
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
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        self.progress_updated.emit(30)

        binning_config_path = _resolve_binning_config_path()
        predict_status_module.BINNING_CONFIG_PATH = binning_config_path
        binning_config = predict_status_module.load_binning_config(binning_config_path)
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
        try:
            report_text = self._generate_single_report(prediction, probs, binning_config, data_dict)
            report_path = os.path.join(RESULT_DIR, "single_prediction_report.txt")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
        except Exception as exc:
            if self.log_message:
                self.log_message.emit(f"⚠️ 生成单次报告失败: {exc}")
        self.single_prediction_finished.emit(prediction, data_dict, probs)

    def _generate_single_report(self, prediction, probs, binning_config, input_data):
        target_info = binning_config.get("data_info", {}).get("target_info", {})
        normal_value = target_info.get("normal_value", "")
        network_rules_path = os.path.join(RESULT_DIR, "network_rules_with_mapping.json")
        network_rules = []
        if os.path.exists(network_rules_path):
            try:
                network_rules = predict_status_module.load_network_rules(network_rules_path)
            except Exception:
                network_rules = []
        key_parameters = predict_status_module.get_key_parameters_for_status(prediction, network_rules)
        key_params_str = "、".join(key_parameters) if key_parameters else "无"

        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        report_lines = [
            "质量评价报告",
            "===========================",
            f"最可能的状态是: {prediction}，概率为{sorted_probs[0][1]:.4f}" if sorted_probs else f"最可能的状态是: {prediction}",
            f"需要特别关注的参数为: {key_params_str}",
            "",
            "各状态的预测概率:"
        ]
        for status, prob in sorted_probs:
            suffix = " (最高概率)" if status == prediction else ""
            report_lines.append(f"  {status}: {prob:.4f}{suffix}")

        report_lines.append("")
        report_lines.append("输入数据:")
        for key, value in input_data.items():
            report_lines.append(f"  {key}: {value}")

        if normal_value:
            report_lines.append(f"\n正常状态参考值: {normal_value}")

        return "\n".join(report_lines)
