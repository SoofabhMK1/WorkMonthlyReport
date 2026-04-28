import json
import os
import traceback
from openai import OpenAI
from core.config import config
import markdown

class ReportAnalyzerAgent:
    def __init__(self):
        self.api_key = config.get_api_key()
        self.base_url = config.get_base_url()
        self.llm_params = config.llm_settings
        
        self.model = self.llm_params.get('model', 'gpt-4o')
        
        # 读取提示词
        prompt_path = config.prompt_path
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            self.prompt_template = None
            print(f"❌ 严重错误: 找不到提示词文件 {prompt_path}")

    def generate_insight(self, target_month: str, kpi_data: dict) -> str:
        print(f"🤖 准备调用 {self.model} 进行数据分析...")
        
        # 拦截 1：检查 API Key
        if not self.api_key:
            error_msg = "⚠️ API Key 缺失！请检查 .env 文件是否配置正确。"
            print(f"❌ {error_msg}")
            return f"<div style='color:#dc2626; font-weight:bold;'>{error_msg}</div>"
            
        # 拦截 2：检查提示词
        if not self.prompt_template:
             return "<div style='color:#dc2626; font-weight:bold;'>⚠️ 找不到提示词文件 (prompt_template.md)，请检查目录结构。</div>"

        # 组装数据 (这部分与之前一致)
        current_data = {
            "总收入": kpi_data["kpis"]["total_revenue"]["value"],
            "总成本": kpi_data["kpis"]["total_cost"]["value"],
            "净利润": kpi_data["kpis"]["net_profit"]["value"],
            "总人次": kpi_data["kpis"]["total_visits"]["value"]
        }
        historical_data = {
            "总收入同比": kpi_data["kpis"]["total_revenue"]["yoy"],
            "净利润同比": kpi_data["kpis"]["net_profit"]["yoy"]
        }
        department_details = kpi_data.get("department_details", {})

        final_prompt = self.prompt_template.format(
            target_month=target_month,
            current_data=json.dumps(current_data, ensure_ascii=False),
            historical_data=json.dumps(historical_data, ensure_ascii=False),
            department_details=json.dumps(department_details, ensure_ascii=False)
        )

        # 开始调用 API
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        try:
            print("⏳ 正在等待大模型响应 (可能需要 5-15 秒)...")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个严谨的数据分析师，只输出最终分析结果。"},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=self.llm_params.get('temperature', 0.2),
                timeout=self.llm_params.get('timeout', 60) # 强制设置超时，防止无限死等
            )
            
            insight_text = response.choices[0].message.content.strip()
            
            # 去掉思考模型的思考过程标签
            import re
            insight_text = re.sub(r'<think>[\s\S]*?</think>', '', insight_text, flags=re.IGNORECASE)
            insight_text = re.sub(r'<think>[\s\S]*?', '', insight_text, flags=re.IGNORECASE)
            
            # 拦截 3：模型返回了空数据
            if not insight_text:
                return "<div style='color:#d97706; font-weight:bold;'>⚠️ 大模型调用成功，但返回了空内容，请检查 Prompt 是否合理。</div>"
                
            print("✅ 大模型分析生成成功！")
            html_insight = markdown.markdown(insight_text, extensions=['extra', 'nl2br'])
            
            return html_insight
            
        except Exception as e:
            # 拦截 4：网络错误、模型名字填错、超时等综合异常
            error_details = traceback.format_exc()
            print(f"❌ 大模型调用发生异常:\n{error_details}")
            
            # 返回一段红色的 HTML 以便直接渲染在截图上
            return (
                f"<div style='color:#dc2626;'>"
                f"<b>⚠️ 大模型接口调用失败</b><br>"
                f"错误原因：{str(e)}<br>"
                f"<span style='font-size:12px; color:#ef4444;'>请检查控制台日志获取详细报错。</span>"
                f"</div>"
            )