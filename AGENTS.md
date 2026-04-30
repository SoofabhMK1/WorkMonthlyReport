# 🏥 SIIC Report Agent (上海上实健康医疗运营月报生成系统)

## 🎯 Project Overview (项目概述)
本项目是一个高度解耦的自动化数据报告系统。系统通过读取底层 Excel/CSV 业财数据，经由 Pandas 进行多维聚合计算，调用 LLM (大语言模型) 提取业务异常与归因，最终通过 Jinja2 + Tailwind CSS 组装为 HTML，并利用 Playwright 截取为适合移动端（如钉钉、微信）阅读的高清长图。

## 🏗️ Architecture & Modules (架构与模块解耦)
系统遵循严格的"单一职责原则 (SRP)"，模块间通过纯 JSON 字典（数据契约）进行通信。

1. **数据接入层 (`core/data_loader.py`)**：负责读取 `data/数据.xlsx`，基于 `config.yaml` 中的数据源映射配置完成格式清洗和校验。
2. **业务逻辑层（KPI 服务模块化拆分）**：
   - `core/kpi_base.py`：基础工具，时间窗口、安全计算、过滤函数
   - `core/kpi_summary.py`：大盘 KPI，总收入/成本/利润/人次等
   - `core/kpi_trend.py`：趋势 KPI，12个月收入成本趋势
   - `core/kpi_department.py`：科室 KPI，明细/图表/绩效卡片
   - `core/kpi_service.py`：委托调用层，组装各模块输出为统一契约
3. **数据校验层 (`core/validators.py`)**：Schema 校验、KPI 结果合理性校验
4. **AI 分析层 (`core/llm_agent.py`)**：调用大模型 API（基于 `config.yaml` 切换提供商），根据清洗后的数据契约进行异常洞察，并将结果由 Markdown 解析为 HTML。
5. **表现渲染层 (`templates/report.html` & `core/renderer.py`)**：使用 Jinja2 填词，Tailwind CSS 排版，ECharts 绑订数据图表，最后由 Playwright 启动无头 Chromium（开启 Retina 2倍缩放）渲染高清长图。

## 📂 Directory Structure (目录结构)
```text
siic-report-agent/
├── .env                    # 机密配置 (API Keys, 严禁提交)
├── config.yaml             # 业务与模型配置 (模型切换、温度、超时、数据源映射)
├── AGENTS.md               # 本文件，AI 上下文与项目规约
├── main.py                 # 主调度管道
├── data/
│   └── 数据.xlsx           # 原始数据源 (含：大类、二级分类、项目、科室、值)
├── core/
│   ├── config.py           # 统一配置加载器
│   ├── schema.py           # 数据源映射配置（列名映射、科室列表）
│   ├── data_loader.py      # 数据读取与校验
│   ├── validators.py       # 数据校验层
│   ├── kpi_base.py         # KPI 基础工具
│   ├── kpi_summary.py      # 大盘 KPI
│   ├── kpi_trend.py        # 趋势 KPI
│   ├── kpi_department.py   # 科室 KPI
│   ├── kpi_service.py      # KPI 服务主入口（委托调用层）
│   ├── llm_agent.py        # LLM 调度与 Markdown 解析
│   ├── prompt_template.md  # 独立的 AI 提示词库
│   └── renderer.py         # Playwright 截图服务
├── templates/
│   └── report.html         # 核心 HTML/Tailwind 模板
└── output/                 # 生成的最终长图目录
```

### 运行命令
始终使用 `uv run python main.py` 来运行项目（需要虚拟环境）

## 📜 Data Contracts (核心数据契约)
在编写或修改 HTML 模板时，必须遵循由 `kpi_service.py` 产出的 `report_data` 结构：
```json
{
  "report_month": "2026-03",
  "kpis": {
    "total_revenue": {"value": 10000, "yoy": 5.0, "mom": -1.2},
    "total_cost": {"value": ...},
    "gross_profit": {"value": ...},
    "net_profit": {"value": ...},
    "total_visits": {"value": ...},
    "surgeries": {"value": ...}
  },
  "llm_analysis": "<p>解析好的 HTML 字符串...</p>",
  "revenue_cost_trend": {
    "months": ["2025-04", "2025-05", ...],
    "revenue": [1487.8, 548.1, ...],
    "cost": [1372.3, 801.1, ...]
  },
  "department_scorecards": [
    {
      "name": "整形外科",
      "revenue": 650.0,
      "rev_yoy": 5.2,
      "rev_mom": -1.2,
      "visits": 1200,
      "visits_yoy": 3.5,
      "visits_mom": -2.1,
      "avg_revenue": 5400,
      "cost": 480.0,
      "cost_yoy": 8.1,
      "cost_mom": 2.0,
      "margin": 26.1,
      "cost_ratio": 73.8,
      "cost_structure": [
        {"name": "人力成本", "ratio": 45.2},
        {"name": "医疗变动", "ratio": 35.1}
      ]
    }
  ]
}
```

## ⚠️ Development Rules & Known Pitfalls (开发规约与避坑指南)

### 1. 表现层 (UI/HTML) 规约
* **禁止重度依赖 CDN 稳定性**：在 HTML 的 `<style>` 中必须保留核心类的兜底样式（如 `grid-3-2`），防止 Tailwind 插件因网络原因未加载导致排版全毁。ECharts 已本地内联（`templates/echarts.min.js`），渲染时自动注入到 HTML 中，无需外部依赖。
* **ECharts 渲染**：ECharts 代码在 `render_to_image()` 时动态内联到 HTML 中，脚本放在 `<body>` 末尾直接执行，无需 `DOMContentLoaded` 包裹。
* **移动端排版约束**：外层包装器固定宽度 `800px`。对于并排区块（如科室卡片内的收入与成本），优先使用 `grid grid-cols-2` 而非 `flex`，以防止数据过长撑破布局导致换行失控。
* **Markdown 渲染要求**：`llm_analysis` 必须经过 Python 的 `markdown` 库解析（启用 `extra` 和 `nl2br` 扩展），并在 HTML 中使用 Tailwind Typography 插件的 `prose` 类族（如 `prose prose-sm prose-slate`）进行美化，否则列表和加粗将无法正确显示。

### 2. 逻辑层 (Python) 规约
* **量级碾压防范**：绝不要将千万级数据（如整形外科收入）与百元级数据（如美容中医科成本）放入同一个线性图表中（如 ECharts）。
* **安全性除法**：所有的同环比计算、利润率计算、ARPU 计算必须做分母为 0 的防御性判断，防止遇到新科室或新项目时触发 `ZeroDivisionError`。

### 3. AI 分析引擎规约
* **显式错误拦截**：LLM 调度如果遇到超时、断网或返回为空，必须捕获异常并返回包含错误原因的 HTML 字符串（红色预警），以确保报错信息能直接印在最终长图上，实现“所见即所得”的 Debug。
* **归因数据供给**：不要只喂给 LLM 顶层大盘数据。必须将科室的“量本利”拆解、变动成本的异常增长提供给大模型，促使其进行交叉验证和深度归因。
* **思考模型处理**：如果使用带思考过程的模型（如 MiniMax），需要在解析前过滤掉 <think> 和 </think> 标签内容，防止思考过程出现在最终报告中。
```