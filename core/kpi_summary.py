# 文件：core/kpi_summary.py
# 大盘 KPI 计算 - 总收入、总成本、利润、人次等汇总指标
from core.kpi_base import KPIBase

class KPISummary:
    def __init__(self, dataframe):
        """注入数据源
        Args:
            dataframe: pandas DataFrame，已完成基础清洗
        """
        self.df = dataframe
        self._base = KPIBase()

    def calc_raw_metrics(self, target_date):
        """计算单个月份的基础财务与业务指标
        Args:
            target_date: datetime 对象
        Returns:
            dict: 包含 revenue, total_cost, gross_profit, net_profit, visits, surgeries, new_patients, old_patients
        """
        month_df = self._base.filter_by_time(self.df, target_date)

        if month_df.empty:
            return {
                'revenue': 0, 'total_cost': 0, 'gross_profit': 0, 'net_profit': 0,
                'visits': 0, 'surgeries': 0, 'new_patients': 0, 'old_patients': 0
            }

        revenue = month_df[month_df['大类'] == '收入']['值'].sum()
        total_cost = month_df[month_df['大类'] == '成本']['值'].sum()

        variable_costs = month_df[(month_df['大类'] == '成本') & (month_df['二级分类'].str.contains('变动', na=False))]['值'].sum()
        gross_profit = revenue - variable_costs

        fixed_costs = month_df[(month_df['大类'] == '成本') & (~month_df['二级分类'].str.contains('变动', na=False))]['值'].sum()
        net_profit = gross_profit - fixed_costs

        visits = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '挂号人次')]['值'].sum()
        surgeries = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '手术台数')]['值'].sum()
        new_patients = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '新客人数')]['值'].sum()
        old_patients = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '老客人数')]['值'].sum()

        return {
            'revenue': revenue, 'total_cost': total_cost, 'gross_profit': gross_profit, 'net_profit': net_profit,
            'visits': visits, 'surgeries': surgeries, 'new_patients': new_patients, 'old_patients': old_patients
        }

    def generate_summary(self, target_month: str) -> dict:
        """生成大盘 KPI 数据（包含同环比）
        Args:
            target_month: 目标月份，格式 "YYYY-MM"
        Returns:
            dict: kpis 结构，符合 report_data 契约
        """
        times = self._base.get_time_windows(target_month)
        cur = self.calc_raw_metrics(times['current'])
        mom = self.calc_raw_metrics(times['mom'])
        yoy = self.calc_raw_metrics(times['yoy'])

        return {
            "total_revenue": {
                "value": cur['revenue'],
                "yoy": self._base.calc_growth(cur['revenue'], yoy['revenue']),
                "mom": self._base.calc_growth(cur['revenue'], mom['revenue'])
            },
            "total_cost": {
                "value": cur['total_cost'],
                "yoy": self._base.calc_growth(cur['total_cost'], yoy['total_cost']),
                "mom": self._base.calc_growth(cur['total_cost'], mom['total_cost'])
            },
            "gross_profit": {
                "value": cur['gross_profit'],
                "yoy": self._base.calc_growth(cur['gross_profit'], yoy['gross_profit']),
                "mom": self._base.calc_growth(cur['gross_profit'], mom['gross_profit'])
            },
            "net_profit": {
                "value": cur['net_profit'],
                "yoy": self._base.calc_growth(cur['net_profit'], yoy['net_profit']),
                "mom": self._base.calc_growth(cur['net_profit'], mom['net_profit'])
            },
            "total_visits": {
                "value": cur['visits'],
                "yoy": self._base.calc_growth(cur['visits'], yoy['visits']),
                "mom": self._base.calc_growth(cur['visits'], mom['visits'])
            },
            "surgeries": {
                "value": cur['surgeries'],
                "yoy": self._base.calc_growth(cur['surgeries'], yoy['surgeries']),
                "mom": self._base.calc_growth(cur['surgeries'], mom['surgeries'])
            },
            "new_patients": {
                "value": cur['new_patients'],
                "yoy": self._base.calc_growth(cur['new_patients'], yoy['new_patients']),
                "mom": self._base.calc_growth(cur['new_patients'], mom['new_patients'])
            },
            "old_patients": {
                "value": cur['old_patients'],
                "yoy": self._base.calc_growth(cur['old_patients'], yoy['old_patients']),
                "mom": self._base.calc_growth(cur['old_patients'], mom['old_patients'])
            }
        }