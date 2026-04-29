# 文件：core/kpi_service.py
# KPI 服务主入口（委托调用层）- 保持原有接口，向后兼容
from core.kpi_summary import KPISummary
from core.kpi_trend import KPITrend
from core.kpi_department import KPIDepartment

class MonthlyKPIService:
    def __init__(self, dataframe):
        """注入数据源
        Args:
            dataframe: pandas DataFrame，已完成基础清洗
        """
        self.df = dataframe
        self._summary = KPISummary(dataframe)
        self._trend = KPITrend(dataframe)
        self._department = KPIDepartment(dataframe)

    def generate_report_data(self, target_month: str) -> dict:
        """组装最终数据契约（保持原有接口）
        Args:
            target_month: 目标月份，格式 "YYYY-MM"
        Returns:
            dict: 完整的 report_data 结构
        """
        kpis = self._summary.generate_summary(target_month)
        dept_data = self._department.generate_department_data(target_month)
        trend_data = self._trend.generate_trend(target_month)

        return {
            "report_month": target_month,
            "kpis": kpis,
            "department_details": dept_data["department_details"],
            "department_chart_data": dept_data["department_chart_data"],
            "department_scorecards": dept_data["department_scorecards"],
            "revenue_cost_trend": trend_data
        }