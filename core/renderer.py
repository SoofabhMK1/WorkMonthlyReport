from playwright.sync_api import sync_playwright
import os

class ReportRenderer:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def render_to_image(self, html_content: str, filename: str):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # 开启 2 倍采样确保清晰度
            context = browser.new_context(
                viewport={'width': 800, 'height': 1200},
                device_scale_factor=2
            )
            page = context.new_page()
            page.set_content(html_content)
            
            # 【重要】等待网络空闲，确保 Tailwind 和 字体加载完成
            page.wait_for_load_state("networkidle")
            # 【可选】针对复杂的图表，再强行等 500 毫秒
            page.wait_for_timeout(500)
            
            page.screenshot(path=f"output/{filename}", full_page=True)
            browser.close()
            print("✅ 高清渲染完成！")