import html
import os
import re
import time
from typing import Dict, List
from PySide6.QtWidgets import QFileDialog
import shutil
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QObject

from common.utils import show_dialog, get_bayesian_root
from docx import Document


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
            # First, generate the docx report so it's available for asset building
            try:
                from Bayesian_1130.generate_report import main as generate_docx_report
                generate_docx_report()
            except Exception as doc_exc:
                show_dialog(self._parent, f"在后台生成 Word 报告失败:\n{doc_exc}", "警告")
            
            # Then, build the HTML content, which can now find the generated docx
            html_content = self._build_html_from_assets(bayesian_root)

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

        today_str = datetime.now().strftime('%Y-%m-%d')
        default_folder_name = f"装备使用质量评价分析报告_{today_str}"
        default_save_path = Path.home() / default_folder_name

        target_path, _ = QFileDialog.getSaveFileName(
            self._parent,
            "选择导出文件夹名称",
            str(default_save_path),
            "All Files (*)",
        )

        if not target_path:
            return

        target_p = Path(target_path)
        # Use the name provided by the user as the folder name
        export_dir = target_p.parent / target_p.stem
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            show_dialog(self._parent, f"创建导出文件夹失败：\n{export_dir}\n\n错误: {e}", "错误")
            return

        source_assets = self._get_asset_paths(bayesian_root)
        try:
            for asset_path in source_assets:
                if asset_path and asset_path.exists():
                    dest_path = Path(shutil.copy2(asset_path, export_dir))
                    # Ensure exported Word 报告的文件时间为最新，避免旧时间戳
                    if asset_path.suffix.lower() == ".docx":
                        now = time.time()
                        try:
                            os.utime(dest_path, (now, now))
                        except OSError:
                            pass
                else:
                    # Raise a more informative error if a critical asset is missing during copy
                    if asset_path:
                         raise FileNotFoundError(f"源文件在复制时丢失: {asset_path.name}")

        except (shutil.Error, FileNotFoundError) as e:
            show_dialog(self._parent, f"复制文件到导出目录时出错：\n{e}", "错误")
            return

        show_dialog(
            self._parent,
            "报告资产导出成功！\n\n"
            f"所有文件已保存至：\n{export_dir}",
            "导出成功",
        )

    def _build_html_from_assets(self, root_dir: str) -> str:
        apriori_dir = os.path.join(root_dir, "result", "apriori_results")
        bayesian_dir = os.path.join(root_dir, "result", "bayesian_results")
        report_path = os.path.join(bayesian_dir, "prediction_report.txt")
        
        report_docx_path = self._find_latest_report_docx(Path(root_dir))
        doc_path_str = str(report_docx_path) if report_docx_path else ""


        apriori_images = [
            ("故障预测规则提升度.png", "故障预测规则提升度对比"),
            ("离散化方法规则数量对比.png", "各离散化方法生成规则数量对比"),
            ("离散化方法执行时间对比.png", "各离散化方法执行时间对比"),
            ("离散化方法性能综合对比.png", "离散化方法性能综合对比（执行时间 vs 规则数量）"),
        ]
        
        bayesian_images = [
            ("bn_structure.png", "贝叶斯网络结构图"),
            ("confusion_matrix.png", "混淆矩阵"),
        ]

        prediction_data = self._parse_prediction_report(report_path)

        # --- Reverted to simple and reliable style block ---
        style_block = """
        <style>
            .section-title {
                font-size: 14pt;
                font-weight: bold;
                color: #34495e;
                margin: 0 0 10px 0;
                padding-bottom: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            img { /* Directly styling the img tag */
                width: 80%;
                max-width: 80%;
                height: auto;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
                background: #fff;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .caption { /* Caption styling */
                font-size: 10pt;
                font-weight: bold;
                text-align: center;
                color: #34495e;
                margin-bottom: 15px;
            }
            table { width:100%; border-collapse:collapse; margin:15px 0; font-size:9.5pt; }
            table th { background:#f2f2f2; padding:8px; border-bottom:2px solid #ccc; text-align:left; }
            table td { padding:8px; border-bottom:1px solid #eee; }
            .placeholder { margin:10px 0; padding:10px; border-left:4px solid #fbc02d; color:#7f6000; }
            .docx-tip { font-size:9pt; color:#7f8c8d; margin-top:20px; text-align:center; }
        </style>
        """

        html_parts = ["<html><head>", style_block, "</head><body>"]
        html_parts.append("<div style=\"font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;\">")
        
        # --- Section 1: Apriori ---
        html_parts.append('<div style="margin-bottom: 12px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px;">')
        html_parts.append('<div class="section-title">🔍 Apriori 数据挖掘分析</div>')
        html_parts.append("<p>本部分对不同离散化方法在 Apriori 算法中的性能进行评估，包括生成规则的数量、执行时间以及综合性能对比。</p>")
        for filename, caption in apriori_images:
            path = os.path.join(apriori_dir, filename)
            if os.path.exists(path):
                img_src = path.replace("\\\\", "/")
                # Reverted HTML structure for images
                html_parts.append('<div style="margin-top:20px;">')
                html_parts.append(f'<p class="caption">{caption}</p>')
                html_parts.append(f"<center><img src='file:///{img_src}' alt='{caption}' /></center>")
                html_parts.append("</div>")
                html_parts.append("<br>")
            else:
                html_parts.append(f"<div class='placeholder'>[缺失图片: {filename}]</div>")
        html_parts.append("</div>")

        # --- Section 2: Bayesian ---
        html_parts.append('<div style="margin-bottom: 12px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px;">')
        html_parts.append('<div class="section-title">🧠 贝叶斯网络分析</div>')
        html_parts.append("<p>本部分展示了基于贝叶斯网络模型的设备状态预测结果，包括网络结构、模型性能评估和详细分类报告。</p>")
        for filename, caption in bayesian_images:
            path = os.path.join(bayesian_dir, filename)
            if os.path.exists(path):
                img_src = path.replace("\\\\", "/")
                # Reverted HTML structure for images
                html_parts.append('<div style="margin-top:20px;">')
                html_parts.append(f'<p class="caption">{caption}</p>')
                html_parts.append(f"<center><img src='file:///{img_src}' alt='{caption}' /></center>")
                html_parts.append("</div>")
                html_parts.append("<br>")
            else:
                html_parts.append(f"<div class='placeholder'>[缺失图片: {filename}]</div>")

        if prediction_data:
            html_parts.append('<div class="section-title" style="margin-top:15px;">📊 模型性能评估报告</div>')
            if prediction_data.get("accuracy") is not None:
                html_parts.append(
                    f"<p>模型整体准确率为：<strong>{prediction_data['accuracy']:.4f}</strong></p>"
                )
            html_parts.append(self._build_class_table(prediction_data.get("classes", [])))
            html_parts.append(
                "<p><strong>结论：</strong>模型在“正常运行”等主流状态上表现稳定，"
                "但面对样本量较小的故障类别时仍存在一定的不确定性，建议结合业务经验继续优化。</p>"
            )
        else:
            html_parts.append("<div class='placeholder'>[预测报告缺失或无法解析]</div>")
        html_parts.append("</div>")


        if doc_path_str and os.path.exists(doc_path_str):
            html_parts.append(
                f"<p class='docx-tip'>完整的 Word 版本报告已保存在：{html.escape(doc_path_str)}</p>"
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
        acc_match = re.search(r"\u603b\u4f53\u51c6\u786e\u7387[\uff1a:\s]*([0-9.]+)", content)
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
    
    def _find_latest_report_docx(self, root_dir: Path) -> Path | None:
        """Finds the most recently modified report docx file."""
        latest_file = None
        latest_time = 0
        
        # Search for new format
        for file_path in root_dir.glob("装备使用质量评价分析报告_*.docx"):
            try:
                mtime = file_path.stat().st_mtime
                if mtime > latest_time:
                    latest_time = mtime
                    latest_file = file_path
            except FileNotFoundError:
                continue
        
        # If no new format found, check for the old format as a fallback
        if not latest_file:
            old_file = root_dir / "故障预测分析报告.docx"
            if old_file.exists():
                return old_file

        return latest_file

    def _set_loading(self, is_loading: bool, title: str = "", content: str = ""):
        if hasattr(self._parent, "show_state_tooltip"):
            if is_loading:
                self._parent.show_state_tooltip(title, content)
            else:
                self._parent.close_state_tooltip()

    def _get_asset_paths(self, root_dir):
        """获取所有报告资产的路径列表"""
        root_path = Path(root_dir)
        apriori_dir = root_path / "result" / "apriori_results"
        bayesian_dir = root_path / "result" / "bayesian_results"
        
        report_docx_path = self._find_latest_report_docx(root_path)

        paths = [
            apriori_dir / "故障预测规则提升度.png",
            apriori_dir / "离散化方法规则数量对比.png",
            apriori_dir / "离散化方法执行时间对比.png",
            apriori_dir / "离散化方法性能综合对比.png",
            bayesian_dir / "bn_structure.png",
            bayesian_dir / "confusion_matrix.png",
            bayesian_dir / "prediction_report.txt",
        ]
        if report_docx_path:
            paths.append(report_docx_path)
        
        return paths

    def _check_required_assets(self, root_dir: str, check_docx=False):
        root_path = Path(root_dir)
        requirements = self._get_asset_paths(root_path)
        
        # Find the docx path from the requirements list to decide whether to check it
        docx_in_list = any(str(p).endswith('.docx') for p in requirements)

        if not check_docx:
            requirements = [p for p in requirements if not str(p).endswith('.docx')]

        missing = []
        for path in requirements:
            if not path or not path.exists():
                # Provide a more user-friendly description for missing files
                if path:
                    description = f"{path.parent.name}中的{path.name}"
                    missing.append(description)
        
        # Special check for docx if it was required but not found by _get_asset_paths
        if check_docx and not docx_in_list:
            missing.append("Bayesian_1130中的装备使用质量评价分析报告_*.docx")
            
        return missing
