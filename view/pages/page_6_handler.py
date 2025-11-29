import html
import os
import re
from typing import Dict, List
from PySide6.QtWidgets import QFileDialog
import shutil
from pathlib import Path

from PySide6.QtCore import QObject

from common.utils import show_dialog, get_bayesian_root


class Page6Handler(QObject):
    """读取磁盘结果并生成富文本报告"""

    def __init__(self, parent: "Page6"):
        super().__init__(parent)
        self._parent = parent

    def generate_report(self):
        bayesian_root = str(get_bayesian_root())
        missing_assets = self._check_required_assets(bayesian_root)
        if missing_assets:
            missing_text = "\n".join(f"- {item}" for item in missing_assets)
            show_dialog(
                self._parent,
                "报告生成需要先完成前置步骤，请依次完成：\n"
                "1. Page1 导入并配置数据集\n"
                "2. Page2 完成规则挖掘（生成离散化图表）\n"
                "3. Page3 构建贝叶斯网络（生成网络结构图）\n"
                "4. Page4 进行批量质量评估（输出预测报告与混淆矩阵）\n\n"
                f"以下文件缺失：\n{missing_text}",
                "提示",
            )
            return

        self._set_loading(True, "正在汇总报告", "正在读取最新结果，请稍候…")
        self._parent.pushButton_export.setEnabled(False)

        try:
            html_content = self._build_html_from_assets(bayesian_root)
            # --- new code added ---
            try:
                from Bayesian_1130.generate_report import main as generate_docx_report
                generate_docx_report()
            except Exception as doc_exc:
                # If docx generation fails, show a non-blocking warning but continue
                show_dialog(self._parent, f"在后台生成 Word 报告失败:\n{doc_exc}", "警告")
            # --- end of new code ---
        except Exception as exc:
            show_dialog(self._parent, f"生成报告内容失败:\n{exc}", "错误")
            self._parent.textEdit.clear()
        else:
            self._parent.textEdit.setHtml(html_content)
        finally:
            self._set_loading(False)
            self._parent.pushButton_export.setEnabled(True)

    def save_report_assets(self):
        """导出报告所需的所有资产文件"""
        bayesian_root = get_bayesian_root()
        
        # 1. 检查所有必需的文件是否都已生成
        missing_assets = self._check_required_assets(str(bayesian_root), check_docx=True)
        if missing_assets:
            missing_text = "\n".join(f"- {item}" for item in missing_assets)
            show_dialog(
                self._parent,
                "无法导出，因为报告资产不完整。\n"
                "请先点击“生成质量评估报告”按钮以确保所有文件都已就绪。\n\n"
                f"以下文件缺失：\n{missing_text}",
                "错误",
            )
            return

        # 2. 弹出文件保存对话框
        default_save_path = Path.home() / "故障预测分析报告"
        target_path, _ = QFileDialog.getSaveFileName(
            self._parent,
            "选择导出位置和报告名称",
            str(default_save_path),
            "All Files (*)",
        )

        if not target_path:
            return  # 用户取消

        # 3. 创建目标文件夹
        # 使用用户输入的文件名（不含扩展名）作为文件夹名
        target_p = Path(target_path)
        export_dir = target_p.parent / target_p.stem
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            show_dialog(self._parent, f"创建导出文件夹失败：\n{export_dir}\n\n错误: {e}", "错误")
            return

        # 4. 定义并复制所有资产文件
        source_assets = self._get_asset_paths(bayesian_root)
        try:
            for asset_path in source_assets:
                if asset_path.exists():
                    shutil.copy(asset_path, export_dir)
                else:
                    # 理论上 _check_required_assets 已经检查过，但作为安全措施
                    raise FileNotFoundError(f"源文件在复制时丢失: {asset_path}")
        except (shutil.Error, FileNotFoundError) as e:
            show_dialog(self._parent, f"复制文件到导出目录时出错：\n{e}", "错误")
            return

        # 5. 显示成功信息
        show_dialog(
            self._parent,
            "报告资产导出成功！\n\n" 
            f"所有文件已保存至：\n{export_dir}",
            "导出成功",
        )

    # ----------------- HTML 组装 -----------------

    def _build_html_from_assets(self, root_dir: str) -> str:
        apriori_dir = os.path.join(root_dir, "result", "apriori_results")
        bayesian_dir = os.path.join(root_dir, "result", "bayesian_results")
        report_path = os.path.join(bayesian_dir, "prediction_report.txt")
        doc_path = os.path.join(root_dir, "故障预测分析报告.docx")

        apriori_images = [
            ("故障预测规则提升度.png", "故障预测规则提升度对比"),
            ("离散化方法规则数量对比.png", "各离散化方法生成规则数量对比"),
            ("离散化方法执行时间对比.png", "各离散化方法执行时间对比"),
            ("离散化方法性能综合对比.png", "离散化方法性能综合对比（执行时间 vs 规则数量）"),
        ]

        prediction_data = self._parse_prediction_report(report_path)

        style_block = """
        <style>
            body { font-family: 'Microsoft YaHei','Segoe UI',sans-serif; background:#f6f8fb; }
            .report { font-size:11pt; line-height:1; color:#263238; padding:12px 6%; width:100%; box-sizing:border-box; }
            .report-title { font-size:18px; font-weight:bold; color:#0d47a1; border-bottom:2px solid #dfe6f0; padding-bottom:6px; margin-bottom:12px; }
            .section-title { font-size:14pt; color:#1565c0; margin:18px 0 12px; border-left:4px solid #5c9ded; padding-left:10px; font-weight: bold;}
            .sub-title { font-size:12pt; color:#1e88e5; margin:16px 0 8px; display:block; text-align:left; font-weight: bold;}
            .intro { text-indent:2em; margin:6px 0 10px; }
            .img-block { margin:18px 0; text-align:center; }
            .figure-title { width:90%; margin:0 auto 8px; font-size:30pt; color:#0d2f4f; font-weight:600; text-align:left; }
            .img-block img { width:90%; max-width:90%; height:auto; border-radius:10px; border:1px solid #e3e9ef; background:#fff; padding:6px; box-shadow:0 2px 6px rgba(0,0,0,0.05); }
            table { width:100%; border-collapse:collapse; margin:12px 0; font-size:10.5pt; }
            table th { background:#e3f2fd; padding:8px; color:#1a237e; border:1px solid #dfe6f0; }
            table td { border:1px solid #e3e9ef; padding:8px; background:#fff; }
            table tbody tr:nth-child(odd) td { background:#fdfdfd; }
            .placeholder { margin:10px 0; padding:10px; background:#fff9c4; border-left:4px solid #fbc02d; color:#7f6000; }
            .docx-tip { font-size:10pt; color:#546e7a; margin-top:12px; word-break:break-all; }
        </style>
        """

        html_parts = ["<html><head>", style_block, "</head><body><div class='report'>"]
        html_parts.append('<div class="report-title">质量评价模型分析报告</div>')
        html_parts.append(
            "<p class='intro'>以下内容直接取自最新一次 Apriori 规则挖掘与贝叶斯网络评估的结果，"
            "展示顺序与 CLI 版报告保持一致。</p>"
        )

        # Section 1
        html_parts.append("<div class='section-title'>一、Apriori 数据挖掘板块</div>")
        html_parts.append(
            "<p class='intro'>本部分对不同离散化方法在 Apriori 算法中的性能进行了全面评估，"
            "包括生成规则的数量、执行时间以及综合性能对比。</p>"
        )
        for filename, caption in apriori_images:
            path = os.path.join(apriori_dir, filename)
            if os.path.exists(path):
                img_src = path.replace("\\\\", "/")
                html_parts.append("<div class='img-block'>")
                html_parts.append(f"<div class='sub-title'>{caption}</div>")
                html_parts.append("<br>")
                html_parts.append(f"<center><img src='file:///{img_src}' alt='{caption}' /></center>")
                html_parts.append("</div>")
            else:
                html_parts.append(f"<div class='placeholder'>[缺失图片: {filename}]</div>")

        # Section 2
        html_parts.append("<div class='section-title'>二、贝叶斯网络板块</div>")
        html_parts.append(
            "<p class='intro'>本部分展示了基于贝叶斯网络模型的设备状态预测结果，"
            "包括网络结构、模型性能评估和详细分类报告。</p>"
        )

        for filename, caption in [
            ("bn_structure.png", "贝叶斯网络结构图"),
            ("confusion_matrix.png", "混淆矩阵"),
        ]:
            path = os.path.join(bayesian_dir, filename)
            if os.path.exists(path):
                img_src = path.replace("\\\\", "/")
                html_parts.append("<div class='img-block'>")
                html_parts.append(f"<div class='sub-title'>{caption}</div>")
                html_parts.append("<br>")
                html_parts.append(f"<center><img src='file:///{img_src}' alt='{caption}' /></center>")
                html_parts.append("</div>")
            else:
                html_parts.append(f"<div class='placeholder'>[缺失图片: {filename}]</div>")

        if prediction_data:
            html_parts.append("<div class='sub-title'>模型性能评估报告</div>")
            if prediction_data.get("accuracy") is not None:
                html_parts.append(
                    f"<p>模型整体准确率为：<strong>{prediction_data['accuracy']:.4f}</strong></p>"
                )
            html_parts.append(self._build_class_table(prediction_data.get("classes", [])))
            html_parts.append(
                "<p class='intro'><strong>结论：</strong>模型在“正常运行”等主流状态上表现稳定，"
                "但面对样本量较小的故障类别时仍存在一定的不确定性，建议结合业务经验继续优化。</p>"
            )
        else:
            html_parts.append("<div class='placeholder'>[预测报告缺失或无法解析]</div>")

        if os.path.exists(doc_path):
            html_parts.append(
                f"<p class='docx-tip'>完整的 Word 版本报告已保存在：{html.escape(doc_path)}</p>"
            )

        html_parts.append("</div></body></html>")
        return "".join(html_parts)

    def _build_class_table(self, classes):
        if not classes:
            return "<div class='placeholder'>预测报告中未找到分类指标。</div>"

        rows = [
            "<table><thead><tr><th>类别</th><th>精确率</th><th>召回率</th>"
            "<th>F1 分数</th><th>支持样本数</th></tr></thead><tbody>"
        ]
        for cls in classes:
            rows.append(
                "<tr>"
                f"<td>{html.escape(cls['name'])}</td>"
                f"<td>{cls['precision']:.2f}</td>"
                f"<td>{cls['recall']:.2f}</td>"
                f"<td>{cls['f1-score']:.2f}</td>"
                f"<td>{cls['support']}</td>"
                "</tr>"
            )
        rows.append("</tbody></table>")
        return "".join(rows)

    def _parse_prediction_report(self, report_path: str):
        if not os.path.exists(report_path):
            return None
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        data = {}
        acc_match = re.search(r"\u603b\u4f53\u51c6\u786e\u7387[：:\s]*([0-9.]+)", content)
        if acc_match:
            data['accuracy'] = float(acc_match.group(1))

        classes = []
        lines = content.splitlines()
        header_found = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if header_found and classes:
                    break
                continue
            if (
                    not header_found
                    and 'precision' in stripped
                    and 'recall' in stripped
                    and 'f1-score' in stripped
                    and 'support' in stripped
            ):
                header_found = True
                continue
            if header_found:
                parts = stripped.split()
                if len(parts) < 5:
                    continue
                label = parts[0]
                if label in {'accuracy', 'macro', 'weighted'} or label.startswith('macro'):
                    continue
                try:
                    precision, recall, f1_score, support = map(float, parts[1:5])
                except ValueError:
                    continue
                classes.append({
                    'name': label,
                    'support': int(support),
                    'precision': precision,
                    'recall': recall,
                    'f1-score': f1_score
                })

        if 'accuracy' not in data:
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('accuracy'):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        try:
                            data['accuracy'] = float(parts[1])
                        except ValueError:
                            pass
                    break

        if not classes:
            class_blocks = re.findall(
                r"([\u4e00-\u9fa5A-Za-z0-9_]+)\s*:\s*\u652f\u6301\u6837\u672c.*?([0-9.]+).*?\u7cbe\u786e\u7387.*?([0-9.]+).*?\u53ec\u56de\u7387.*?([0-9.]+).*?F1.*?([0-9.]+)",
                content,
                re.DOTALL,
            )
            for name, sup, prec, rec, f1 in class_blocks:
                classes.append({
                    'name': name.strip(),
                    'support': int(float(sup)),
                    'precision': float(prec),
                    'recall': float(rec),
                    'f1-score': float(f1)
                })

        if classes:
            data['classes'] = classes

        return data if data else None

    # ----------------- 工具方法 -----------------

    def _set_loading(self, is_loading: bool, title: str = "", content: str = ""):
        if hasattr(self._parent, "show_state_tooltip"):
            if is_loading:
                self._parent.show_state_tooltip(title, content)
            else:
                self._parent.close_state_tooltip()

    def _get_asset_paths(self, root_dir):
        """获取所有报告资产的路径列表"""
        apriori_dir = root_dir / "result" / "apriori_results"
        bayesian_dir = root_dir / "result" / "bayesian_results"
        
        return [
            apriori_dir / "故障预测规则提升度.png",
            apriori_dir / "离散化方法规则数量对比.png",
            apriori_dir / "离散化方法执行时间对比.png",
            apriori_dir / "离散化方法性能综合对比.png",
            bayesian_dir / "bn_structure.png",
            bayesian_dir / "confusion_matrix.png",
            bayesian_dir / "prediction_report.txt",
            root_dir / "故障预测分析报告.docx",
        ]

    def _check_required_assets(self, root_dir: str, check_docx=False):
        root_path = Path(root_dir)
        requirements = self._get_asset_paths(root_path)
        
        # 根据参数决定是否检查 docx 文件
        if not check_docx:
            requirements = [p for p in requirements if not str(p).endswith('.docx')]

        missing = []
        for path in requirements:
            if not path.exists():
                # 提供更友好的描述
                description = f"{path.parent.name}中的{path.name}"
                missing.append(description)
        return missing