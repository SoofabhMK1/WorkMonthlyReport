from playwright.sync_api import sync_playwright
import os

class ReportRenderer:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def render_to_image(self, html_content: str, filename: str):
        # 内联 ECharts，避免外部依赖和路径问题
        echarts_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'echarts.min.js')
        if os.path.exists(echarts_path):
            with open(echarts_path, 'r', encoding='utf-8') as f:
                echarts_code = f.read()
            html_content = html_content.replace('<script src="echarts.min.js"></script>', f'<script>{echarts_code}</script>')

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 800, 'height': 1200},
                device_scale_factor=2
            )
            page = context.new_page()
            page.set_content(html_content)

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            try:
                page.wait_for_selector('#trend-chart canvas', timeout=5000)
                print("✅ ECharts canvas 已渲染")
            except:
                print("❌ ECharts canvas 未找到")

            page.screenshot(path=f"output/{filename}", full_page=True)
            browser.close()
            print("✅ 高清渲染完成！")