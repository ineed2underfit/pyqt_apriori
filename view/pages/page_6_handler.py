import html
import os
import re

from PySide6.QtCore import QObject

from common.utils import show_dialog


class Page6Handler(QObject):
    """读取磁盘结果并生成富文本报告"""

    def __init__(self, parent: "Page6"):
        super().__init__(parent)
        self._parent = parent

    def generate_report(self):
        project_root = os.getcwd()
        missing_assets = self._check_required_assets(project_root)
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
        self._parent.pushButton.setEnabled(False)

        try:
            html_content = self._build_html_from_assets(project_root)
        except Exception as exc:
            show_dialog(self._parent, f"生成报告内容失败:\n{exc}", "错误")
            self._parent.textEdit.clear()
        else:
            self._parent.textEdit.setHtml(html_content)
        finally:
            self._set_loading(False)
            self._parent.pushButton.setEnabled(True)

    # ----------------- HTML 组装 -----------------

    def _build_html_from_assets(self, root_dir: str) -> str:
        apriori_dir = os.path.join(root_dir, "Bayesian_1130", "result", "apriori_results")
        bayesian_dir = os.path.join(root_dir, "Bayesian_1130", "result", "bayesian_results")
        report_path = os.path.join(bayesian_dir, "prediction_report.txt")
        doc_path = os.path.join(root_dir, "Bayesian_1130", "故障预测分析报告.docx")

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
            .report { font-size:11pt; line-height:1.65; color:#263238; padding:12px 18px; }
            .report h1 { font-size:20pt; color:#0d47a1; border-bottom:2px solid #dfe6f0; padding-bottom:6px; margin-bottom:14px; }
            .section-title { font-size:16pt; color:#1565c0; margin:18px 0 6px; border-left:4px solid #5c9ded; padding-left:10px; }
            .sub-title { font-size:13pt; color:#1e88e5; margin:12px 0 4px; }
            .intro { text-indent:2em; margin:8px 0; }
            .img-card { margin:6px 0; padding:8px; background:#fff; border-radius:6px; box-shadow:0 2px 8px rgba(15,76,129,0.05); }
            .img-card h4 { margin:0 0 6px 0; color:#1b5e20; font-weight:600; }
            .img-card img { display:block; width:90%; max-width:90%; margin:0 auto; height:auto; border-radius:6px; border:1px solid #e3e9ef; object-fit:contain; }
            table { width:100%; border-collapse:collapse; margin:12px 0; font-size:10.5pt; }
            table th { background:#e3f2fd; padding:8px; color:#1a237e; border:1px solid #dfe6f0; }
            table td { border:1px solid #e3e9ef; padding:8px; background:#fff; }
            table tbody tr:nth-child(odd) td { background:#fdfdfd; }
            .placeholder { margin:12px 0; padding:10px; background:#fff9c4; border-left:4px solid #fbc02d; color:#7f6000; }
            .docx-tip { font-size:10pt; color:#546e7a; margin-top:12px; }
        </style>
        """

        html_parts = ["<html><head>", style_block, "</head><body><div class='report'>"]
        html_parts.append("<h1>质量评价模型分析报告</h1>")
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
                img_src = path.replace("\\", "/")
                html_parts.append("<div class='img-card'>")
                html_parts.append(f"<h4>{caption}</h4>")
                html_parts.append(f"<img src='file:///{img_src}' alt='{caption}' />")
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
                img_src = path.replace("\\", "/")
                html_parts.append("<div class='img-card'>")
                html_parts.append(f"<h4>{caption}</h4>")
                html_parts.append(f"<img src='file:///{img_src}' alt='{caption}' />")
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
        acc_match = re.search(r"总体准确率[:：]\s*([0-9.]+)", content)
        if acc_match:
            data["accuracy"] = float(acc_match.group(1))

        class_blocks = re.findall(
            r"([\u4e00-\u9fa5A-Za-z0-9_]+)\s*:\s*支持样本数[:：]\s*([0-9.]+).*?"
            r"精确率[:：]\s*([0-9.]+).*?召回率[:：]\s*([0-9.]+).*?F1分数[:：]\s*([0-9.]+)",
            content,
            re.DOTALL,
        )
        classes = []
        for name, sup, prec, rec, f1 in class_blocks:
            classes.append(
                {
                    "name": name.strip(),
                    "support": int(float(sup)),
                    "precision": float(prec),
                    "recall": float(rec),
                    "f1-score": float(f1),
                }
            )
        data["classes"] = classes
        return data

    # ----------------- 工具方法 -----------------

    def _set_loading(self, is_loading: bool, title: str = "", content: str = ""):
        if hasattr(self._parent, "show_state_tooltip"):
            if is_loading:
                self._parent.show_state_tooltip(title, content)
            else:
                self._parent.close_state_tooltip()

    def _check_required_assets(self, root_dir: str):
        apriori_dir = os.path.join(root_dir, "Bayesian_1130", "result", "apriori_results")
        bayesian_dir = os.path.join(root_dir, "Bayesian_1130", "result", "bayesian_results")

        requirements = [
            ("离散化提升图 (Page2)", os.path.join(apriori_dir, "故障预测规则提升度.png")),
            ("规则数量对比图 (Page2)", os.path.join(apriori_dir, "离散化方法规则数量对比.png")),
            ("执行时间对比图 (Page2)", os.path.join(apriori_dir, "离散化方法执行时间对比.png")),
            ("性能综合对比图 (Page2)", os.path.join(apriori_dir, "离散化方法性能综合对比.png")),
            ("贝叶斯网络结构图 (Page3)", os.path.join(bayesian_dir, "bn_structure.png")),
            ("混淆矩阵 (Page4)", os.path.join(bayesian_dir, "confusion_matrix.png")),
            ("批量预测报告 (Page4)", os.path.join(bayesian_dir, "prediction_report.txt")),
        ]

        missing = []
        for description, path in requirements:
            if not os.path.exists(path):
                missing.append(f"{description} -> {path}")
        return missing
