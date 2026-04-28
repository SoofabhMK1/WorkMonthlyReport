import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

class HospitalDataProcessor:
    def __init__(self, file_path):
        """初始化处理器并加载数据"""
        # 加载数据，确保日期列被解析为 datetime 对象
        self.df = pd.read_excel(file_path, parse_dates=['日期'])
        # 填充可能为空的值
        self.df['值'] = pd.to_numeric(self.df['值'], errors='coerce').fillna(0)

    def _get_date_ranges(self, target_month_str):
        """计算当月、上月(环比)、去年同月(同比)的日期"""
        target_date = datetime.strptime(target_month_str, '%Y-%m')
        
        return {
            'current': target_date,
            'mom': target_date - relativedelta(months=1),
            'yoy': target_date - relativedelta(years=1)
        }

    def _calculate_metrics_for_month(self, target_date):
        """核心业务逻辑：计算特定月份的具体财务和业务指标"""
        # 过滤出该月的数据
        month_df = self.df[
            (self.df['日期'].dt.year == target_date.year) & 
            (self.df['日期'].dt.month == target_date.month)
        ]

        if month_df.empty:
            return {'revenue': 0, 'gross_profit': 0, 'net_profit': 0, 'visits': 0}

        # 1. 计算总收入 (假设大类为'收入')
        revenue = month_df[month_df['大类'] == '收入']['值'].sum()

        # 2. 财务分类计算
        # 从样本看，二级分类包含 '运营变动', '医疗变动', '运营房屋物业', '人力成本'
        # 毛利 = 收入 - 变动成本 (包含医疗变动和运营变动)
        variable_costs = month_df[
            (month_df['大类'] == '成本') & 
            (month_df['二级分类'].str.contains('变动', na=False))
        ]['值'].sum()
        gross_profit = revenue - variable_costs

        # 净利 = 毛利 - 固定成本 (人力、房屋物业等其他所有成本)
        fixed_costs = month_df[
            (month_df['大类'] == '成本') & 
            (~month_df['二级分类'].str.contains('变动', na=False))
        ]['值'].sum()
        net_profit = gross_profit - fixed_costs

        # 3. 计算业务指标：总挂号人次
        visits = month_df[
            (month_df['大类'] == '人次') & 
            (month_df['项目'] == '挂号人次')
        ]['值'].sum()

        return {
            'revenue': revenue,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'visits': visits
        }

    def _calculate_growth(self, current, previous):
        """计算增长率，处理除以0的情况"""
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return round(((current - previous) / previous) * 100, 1)

    def generate_kpi_report(self, target_month):
        """生成看板所需的最终数据结构"""
        dates = self._get_date_ranges(target_month)
        
        # 计算三个时间点的指标
        current_metrics = self._calculate_metrics_for_month(dates['current'])
        mom_metrics = self._calculate_metrics_for_month(dates['mom'])
        yoy_metrics = self._calculate_metrics_for_month(dates['yoy'])

        # 构建前端需要的 JSON 结构
        report_data = {
            "report_month": target_month,
            "kpis": {
                "total_revenue": {
                    "value": current_metrics['revenue'],
                    "yoy": self._calculate_growth(current_metrics['revenue'], yoy_metrics['revenue']),
                    "mom": self._calculate_growth(current_metrics['revenue'], mom_metrics['revenue'])
                },
                "gross_profit": {
                    "value": current_metrics['gross_profit'],
                    "yoy": self._calculate_growth(current_metrics['gross_profit'], yoy_metrics['gross_profit']),
                    "mom": self._calculate_growth(current_metrics['gross_profit'], mom_metrics['gross_profit'])
                },
                "net_profit": {
                    "value": current_metrics['net_profit'],
                    "yoy": self._calculate_growth(current_metrics['net_profit'], yoy_metrics['net_profit']),
                    "mom": self._calculate_growth(current_metrics['net_profit'], mom_metrics['net_profit'])
                },
                "total_visits": {
                    "value": current_metrics['visits'],
                    "yoy": self._calculate_growth(current_metrics['visits'], yoy_metrics['visits']),
                    "mom": self._calculate_growth(current_metrics['visits'], mom_metrics['visits'])
                }
            }
        }
        return report_data

# ================= 测试执行 =================
if __name__ == "__main__":
    processor = HospitalDataProcessor('数据.xlsx')
    
    # 为了演示，我们将目标月份设定为您数据中存在的月份，例如 2026-03
    report_json = processor.generate_kpi_report('2026-03')
    
    print(json.dumps(report_json, indent=4, ensure_ascii=False))
    print("数据处理脚本已准备就绪。")