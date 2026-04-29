# 文件：core/kpi_trend.py
# 趋势 KPI 计算 - 12个月收入成本趋势
from core.kpi_base import KPIBase
from dateutil.relativedelta import relativedelta

class KPITrend:
    def __init__(self, dataframe):
        """注入数据源
        Args:
            dataframe: pandas DataFrame，已完成基础清洗
        """
        self.df = dataframe
        self._base = KPIBase()

    def calc_trend(self, target_date, months=12):
        """计算近 N 个月收入与成本趋势
        Args:
            target_date: datetime 对象，基准月份
            months: 趋势月份数量，默认为12
        Returns:
            dict: 包含 months, revenue, cost 三个列表
        """
        trend_data = {"months": [], "revenue": [], "cost": []}

        for i in range(months - 1, -1, -1):
            month_date = target_date - relativedelta(months=i)
            month_df = self._base.filter_by_time(self.df, month_date)

            rev = month_df[month_df['大类'] == '收入']['值'].sum()
            cost = month_df[month_df['大类'] == '成本']['值'].sum()

            trend_data["months"].append(month_date.strftime("%Y-%m"))
            trend_data["revenue"].append(round(rev / 10000, 1))
            trend_data["cost"].append(round(cost / 10000, 1))

        return trend_data

    def generate_trend(self, target_month: str) -> dict:
        """生成收入成本趋势数据
        Args:
            target_month: 目标月份，格式 "YYYY-MM"
        Returns:
            dict: revenue_cost_trend 结构，符合 report_data 契约
        """
        from datetime import datetime
        target_date = datetime.strptime(target_month, '%Y-%m')
        return self.calc_trend(target_date)