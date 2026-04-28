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
            
            # 【重要】等待网络空闲，确保 Tailwind 和 ECharts CDN 加载完成
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            
            # 捕获控制台消息
            def handle_console(msg):
                if msg.type == "error":
                    print(f"⚠️ 控制台错误: {msg.text}")
            page.on("console", handle_console)
            
            # 确保 ECharts canvas 存在
            try:
                page.wait_for_selector('#trend-chart canvas', timeout=5000)
                print("✅ ECharts canvas 已渲染")
            except:
                print("❌ ECharts canvas 未找到")
            
            page.wait_for_timeout(1000)
            
            page.screenshot(path=f"output/{filename}", full_page=True)
            browser.close()
            print("✅ 高清渲染完成！")