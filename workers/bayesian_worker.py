import importlib.util
import io
import os
import shutil
from contextlib import redirect_stdout

from PySide6.QtCore import QObject, Signal


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAYESIAN_ROOT = os.path.join(PROJECT_ROOT, "Bayesian_1130")
DATA_DIR = os.path.join(BAYESIAN_ROOT, "datas")
APRIORI_RESULT_DIR = os.path.join(BAYESIAN_ROOT, "result", "apriori_results")
COMPREHENSIVE_CONFIG_PATH = os.path.join(APRIORI_RESULT_DIR, "完整数据配置.json")
BASIC_BINNING_PATH = os.path.join(APRIORI_RESULT_DIR, "分箱配置.json")
RESULT_DIR = os.path.join(BAYESIAN_ROOT, "result", "bayesian_results")
RULES_CSV_PATH = os.path.join(APRIORI_RESULT_DIR, "关联规则分析结果.csv")

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


build_model_module = _load_module(
    "bayesian_build_model",
    os.path.join("Bayesian", "build_model.py")
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


class BayesianWorker(QObject):
    finished = Signal(str)
    error = Signal(str)
    log_message = Signal(str)
    progress_updated = Signal(int, str)

    def __init__(self, dataset_path):
        super().__init__()
        self.dataset_path = dataset_path

    def run(self):
        try:
            if not os.path.exists(RULES_CSV_PATH):
                raise FileNotFoundError(
                    f"未找到关联规则文件，请先在页面二完成规则挖掘: {RULES_CSV_PATH}"
                )
            binning_config_path = _resolve_binning_config_path()
            if hasattr(build_model_module, "BINNING_CONFIG_PATH"):
                build_model_module.BINNING_CONFIG_PATH = binning_config_path


            self.progress_updated.emit(5, "准备构建贝叶斯网络...")
            train_filename = self._prepare_dataset_file()

            emitter = LogEmitter(self.log_message)

            self.progress_updated.emit(20, "训练贝叶斯网络...")
            with redirect_stdout(emitter):
                build_model_module.build_and_save_bayesian_model(
                    train_filename, model_name="final_bn_model.pkl"
                )

            bn_structure_path = os.path.join(RESULT_DIR, "bn_structure.png")
            if not os.path.exists(bn_structure_path):
                raise FileNotFoundError(f"未找到网络结构图: {bn_structure_path}")

            self.progress_updated.emit(100, "贝叶斯网络构建完成")
            self.finished.emit(bn_structure_path)

        except Exception as exc:
            self.error.emit(str(exc))

    def _prepare_dataset_file(self):
        """确保数据位于 Bayes datas 目录，并返回文件名"""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"数据集不存在: {self.dataset_path}")

        filename = os.path.basename(self.dataset_path)
        target_path = os.path.join(DATA_DIR, filename)

        if os.path.abspath(self.dataset_path) != os.path.abspath(target_path):
            shutil.copy2(self.dataset_path, target_path)

        return filename
