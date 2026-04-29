# 文件：core/kpi_base.py
# KPI 计算基础工具 - 时间窗口、安全计算
from datetime import datetime
from dateutil.relativedelta import relativedelta

class KPIBase:
    @staticmethod
    def get_time_windows(target_month_str):
        """计算时间窗口（本期、环比期、同比期）
        Args:
            target_month_str: 目标月份，格式 "YYYY-MM"
        Returns:
            dict: 包含 current, mom, yoy 三个 datetime 对象
        """
        target_date = datetime.strptime(target_month_str, '%Y-%m')
        return {
            'current': target_date,
            'mom': target_date - relativedelta(months=1),
            'yoy': target_date - relativedelta(years=1)
        }

    @staticmethod
    def calc_growth(current, previous):
        """安全计算增长率（防御除以0）
        Args:
            current: 当前值
            previous: 比较基准值
        Returns:
            float: 增长率百分比，保留1位小数
        """
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return round(((current - previous) / previous) * 100, 1)

    @staticmethod
    def filter_by_time(df, target_date):
        """按年月筛选数据
        Args:
            df: pandas DataFrame，需包含 '日期' 列
            target_date: datetime 对象
        Returns:
            筛选后的 DataFrame
        """
        return df[
            (df['日期'].dt.year == target_date.year) &
            (df['日期'].dt.month == target_date.month)
        ]

    @staticmethod
    def filter_by_category(df, category):
        """按大类筛选数据
        Args:
            df: pandas DataFrame，需包含 '大类' 列
            category: 大类名称（如 '收入'、'成本'、'人次'）
        Returns:
            筛选后的 DataFrame
        """
        return df[df['大类'] == category]

    @staticmethod
    def filter_by_item(df, item):
        """按项目筛选数据
        Args:
            df: pandas DataFrame，需包含 '项目' 列
            item: 项目名称（如 '挂号人次'、'手术台数'）
        Returns:
            筛选后的 DataFrame
        """
        return df[df['项目'] == item]

    @staticmethod
    def filter_by_department(df, department):
        """按科室筛选数据
        Args:
            df: pandas DataFrame，需包含 '科室' 列
            department: 科室名称
        Returns:
            筛选后的 DataFrame
        """
        return df[df['科室'] == department]

    @staticmethod
    def safe_margin(revenue, cost):
        """安全计算利润率
        Args:
            revenue: 收入
            cost: 成本
        Returns:
            float: 利润率百分比，保留1位小数
        """
        if revenue == 0:
            return 0.0 if cost == 0 else -100.0
        return round(((revenue - cost) / revenue) * 100, 1)

    @staticmethod
    def safe_cost_ratio(cost, revenue):
        """安全计算成本占收入比（吃水线）
        Args:
            cost: 成本
            revenue: 收入
        Returns:
            float: 成本比率，限制在 0-100 范围
        """
        if revenue == 0:
            return 100.0
        ratio = round((cost / revenue) * 100, 1)
        return min(ratio, 100)