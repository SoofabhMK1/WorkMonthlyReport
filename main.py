# 文件：main.py
from core.data_loader import ExcelDataLoader
from core.kpi_service import MonthlyKPIService
from core.renderer import ReportRenderer
from core.llm_agent import ReportAnalyzerAgent
from jinja2 import Environment, FileSystemLoader
import os

def main():
    target_month = "2026-03"
    print(f"🚀 开始生成 {target_month} 运营月报...")

    # 1. 加载数据
    loader = ExcelDataLoader(file_path="data/数据.xlsx")
    clean_df = loader.load()

    # 2. 计算指标
    print("正在计算核心 KPI...")
    kpi_service = MonthlyKPIService(clean_df)
    report_data = kpi_service.generate_report_data(target_month)

    # 3. 调用大模型生成洞察
    print("正在召唤 AI 分析师...")
    agent = ReportAnalyzerAgent()
    analysis_html = agent.generate_insight(target_month, report_data)

    print(f"AI 分析长度: {len(analysis_html) if analysis_html else '0'}")
    if len(analysis_html) < 20:
        print(f"AI 原始内容预览: {analysis_html}")

    report_data['llm_analysis'] = analysis_html

    # 4. Jinja2 模板渲染
    print("正在拼接 HTML 模板...")
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('report.html')
    # 渲染出最终的纯 HTML 字符串
    final_html = template.render(data=report_data)

    # 5. Playwright 截图出图
    renderer = ReportRenderer(output_dir="output")
    output_filename = f"运营月报_{target_month}.png"
    renderer.render_to_image(final_html, output_filename)

    print(f"🎉 流程结束！请查看 output/{output_filename}")

if __name__ == "__main__":
    main()