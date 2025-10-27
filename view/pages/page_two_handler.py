from PySide6.QtCore import QObject, QThread, Signal
from components.log_dialog import LogDialog
from workers.apriori_worker import AprioriWorker
from common.utils import show_dialog
import os

# 导入优化脚本中的核心函数
from new_bayesian.dataset.optimal_rules import filter_optimal_rules, get_best_rule_per_fault

class PageTwoHandler(QObject):
    initial_rules_ready = Signal(object)  # 初始规则分析完成信号
    optimized_rules_ready = Signal(object) # 优化规则完成信号

    def __init__(self, parent: 'PageTwo'):
        super().__init__(parent)
        self._parent = parent
        self.log_dialog = None
        self.thread = None
        self.worker = None

    def start_mining(self):
        """开始挖掘规则 (使用线程)"""
        if not self._parent.dataset_path:
            self._parent.on_common_error("请先选择数据集！")
            return

        self._parent.pushButton_2.setEnabled(False)
        self._parent.pushButton.setEnabled(False) # 禁用优化按钮

        try:
            self.log_dialog = LogDialog(title="规则挖掘日志", parent=self._parent)
            self.log_dialog.show()

            self.thread = QThread()
            params = {
                'min_support': self._parent.doubleSpinBox_2.value(),
                'min_confidence': self._parent.doubleSpinBox_3.value(),
                'min_lift': self._parent.doubleSpinBox.value(),
                'auto_optimize': True
            }
            self.worker = AprioriWorker(self._parent.dataset_path, params)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_dialog.append_log)
            self.worker.progress_updated.connect(self._parent.update_progress)
            self.worker.analysis_succeeded.connect(self.on_analysis_success)
            self.worker.analysis_failed.connect(self.on_analysis_error)
            self.worker.analysis_succeeded.connect(self.cleanup_thread)
            self.worker.analysis_failed.connect(self.cleanup_thread)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            self._parent.on_common_error(f"启动分析时出错: {str(e)}")
            self._parent.pushButton_2.setEnabled(True)

    def optimize_rules(self):
        """执行规则优化"""
        main_window = self._parent.window()
        initial_rules = main_window.initial_rules_df

        if initial_rules is None or initial_rules.empty:
            show_dialog(self._parent, "没有可优化的规则，请先提取语料。", "提示")
            return

        # 更新进度条和状态，提供即时反馈
        self._parent.update_progress(0, "准备优化规则...")

        try:
            # 1. 在内存中直接调用优化函数
            optimal_rules = filter_optimal_rules(initial_rules)
            best_rules_df = get_best_rule_per_fault(optimal_rules, by='提升度')

            # 2. 保存优化后的规则到指定文件，为Page3做准备
            # page_two_handler.py -> pages -> view -> 项目根目录 (向上2级)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            save_path = os.path.join(project_root, "new_bayesian", "dataset", "optimal_rules.csv")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            best_rules_df.to_csv(save_path, index=False, encoding='utf-8-sig')

            # 3. 发出信号，将优化后的DataFrame传递给MainWindow
            self.optimized_rules_ready.emit(best_rules_df)

            # 4. 更新PageTwo的UI
            output = self._format_rules_html(best_rules_df, "规则优化完成")
            self._parent.textEdit_3.setHtml(output)
            
            # 5. 更新进度条并显示成功信息
            self._parent.update_progress(100, "规则优化完成")
            show_dialog(self._parent, f"规则优化成功！\n已保存到 {save_path}", "成功")

        except Exception as e:
            self._parent.on_common_error(f"规则优化时出错: {str(e)}")
            self._parent.update_progress(0, "优化失败")

    def on_analysis_success(self, results_df):
        """处理分析成功的结果"""
        # 发送信号给MainWindow，使其可以存储这份原始数据
        self.initial_rules_ready.emit(results_df)
        # 启用优化按钮
        self._parent.pushButton.setEnabled(True)

        try:
            # 使用HTML格式化显示规则
            output = self._format_rules_html(results_df, "初始规则提取完成")
            self._parent.textEdit_3.setHtml(output)
            self._parent.textEdit_3.verticalScrollBar().setValue(0)

        except Exception as e:
            self._parent.on_common_error(f"处理结果时出错: {str(e)}")

    def on_analysis_error(self, error_message):
        self._parent.on_common_error(f"分析过程出错: {error_message}")
        self._parent.progressBar.setValue(0)

    def cleanup_thread(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        if self._parent:
            self._parent.pushButton_2.setEnabled(True)

    def on_parameter_changed(self):
        pass

    def _format_rules_html(self, rules_df, title):
        """将规则DataFrame格式化为美观的HTML显示"""
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'
        
        # 标题
        html += f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #2c3e50; padding: 12px; border-radius: 6px; margin-bottom: 15px; text-align: left;">'
        html += f'<h2 style="margin: 0; font-size: 12pt; font-weight: bold;">📊 {title}</h2>'
        html += f'<p style="margin: 5px 0 0 0; font-size: 9pt; color: #34495e;">共发现 {len(rules_df)} 条规则</p>'
        html += '</div>'
        
        # 规则表格
        html += '<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        
        # 表头
        html += '<thead style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #2c3e50;">'
        html += '<tr>'
        for col in rules_df.columns:
            html += f'<th style="padding: 10px 8px; text-align: left; font-weight: bold; font-size: 9pt;">{col}</th>'
        html += '</tr>'
        html += '</thead>'
        
        # 表格内容
        html += '<tbody>'
        for idx, row in rules_df.iterrows():
            # 交替行颜色
            row_style = "background-color: #f8f9fa;" if idx % 2 == 0 else "background-color: white;"
            html += f'<tr style="{row_style}">'
            
            for col in rules_df.columns:
                value = row[col]
                
                # 特殊处理规则列，添加样式
                if col == '规则':
                    # 高亮显示规则
                    html += f'<td style="padding: 10px 8px; font-family: monospace; font-size: 9pt; color: #2c3e50; background-color: #ecf0f1; border-left: 4px solid #3498db;">{value}</td>'
                elif col in ['支持度', '置信度', '提升度']:
                    # 数值列，右对齐并添加颜色
                    if isinstance(value, (int, float)):
                        if col == '提升度' and value > 2:
                            color = "#27ae60"  # 绿色表示高提升度
                        elif col == '置信度' and value > 0.8:
                            color = "#e67e22"  # 橙色表示高置信度
                        else:
                            color = "#34495e"
                        html += f'<td style="padding: 10px 8px; text-align: right; font-weight: bold; color: {color};">{value:.3f}</td>'
                    else:
                        html += f'<td style="padding: 10px 8px; text-align: right;">{value}</td>'
                else:
                    # 普通列
                    html += f'<td style="padding: 10px 8px; color: #2c3e50;">{value}</td>'
            
            html += '</tr>'
        
        html += '</tbody>'
        html += '</table>'
        
        # 统计信息
        if len(rules_df) > 0:
            html += '<div style="margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); border-radius: 6px;">'
            html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10pt;">📈 规则统计</h3>'
            
            # 计算统计信息
            if '支持度' in rules_df.columns:
                avg_support = rules_df['支持度'].mean()
                html += f'<p style="margin: 5px 0; color: #34495e;"><strong>平均支持度:</strong> {avg_support:.3f}</p>'
            
            if '置信度' in rules_df.columns:
                avg_confidence = rules_df['置信度'].mean()
                html += f'<p style="margin: 5px 0; color: #34495e;"><strong>平均置信度:</strong> {avg_confidence:.3f}</p>'
            
            if '提升度' in rules_df.columns:
                avg_lift = rules_df['提升度'].mean()
                max_lift = rules_df['提升度'].max()
                html += f'<p style="margin: 5px 0; color: #34495e;"><strong>平均提升度:</strong> {avg_lift:.3f}</p>'
                html += f'<p style="margin: 5px 0; color: #34495e;"><strong>最高提升度:</strong> {max_lift:.3f}</p>'
            
            html += '</div>'
        
        html += '</div>'
        return html
