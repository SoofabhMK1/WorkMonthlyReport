# 文件：core/kpi_department.py
# 科室 KPI 计算 - 明细、图表数据、绩效卡片
from core.kpi_base import KPIBase
from core.config import config
from dateutil.relativedelta import relativedelta

class KPIDepartment:
    def __init__(self, dataframe):
        """注入数据源
        Args:
            dataframe: pandas DataFrame，已完成基础清洗
        """
        self.df = dataframe
        self._base = KPIBase()
        self._target_depts = config.target_departments

    def _get_department_data(self, target_date, mom_date, yoy_date):
        """获取各科室在目标月、环比月、同比月的原始数据
        Returns:
            tuple: (cur_df, mom_df, yoy_df, departments)
        """
        cur_df = self._base.filter_by_time(self.df, target_date)
        mom_df = self._base.filter_by_time(self.df, mom_date)
        yoy_df = self._base.filter_by_time(self.df, yoy_date)
        departments = self._target_depts
        return cur_df, mom_df, yoy_df, departments

    def calc_department_details(self, target_date, mom_date):
        """计算各科室的核心指标明细及环比，喂给大模型做归因分析
        Args:
            target_date: datetime 对象，当前月份
            mom_date: datetime 对象，环比月份
        Returns:
            dict: 科室明细数据
        """
        cur_df = self._base.filter_by_time(self.df, target_date)
        mom_df = self._base.filter_by_time(self.df, mom_date)

        dept_details = {}
        for dept in self._target_depts:
            cur_dept = self._base.filter_by_department(cur_df, dept)
            mom_dept = self._base.filter_by_department(mom_df, dept)

            cur_rev = cur_dept[cur_dept['大类'] == '收入']['值'].sum()
            cur_var_cost = cur_dept[(cur_dept['大类'] == '成本') & (cur_dept['二级分类'].str.contains('变动', na=False))]['值'].sum()
            cur_visits = cur_dept[(cur_dept['大类'] == '人次') & (cur_dept['项目'] == '挂号人次')]['值'].sum()

            mom_rev = mom_dept[mom_dept['大类'] == '收入']['值'].sum()
            mom_var_cost = mom_dept[(mom_dept['大类'] == '成本') & (mom_dept['二级分类'].str.contains('变动', na=False))]['值'].sum()

            dept_details[dept] = {
                "本月收入": cur_rev,
                "收入环比": f"{self._base.calc_growth(cur_rev, mom_rev)}%",
                "本月变动成本(耗材等)": cur_var_cost,
                "变动成本环比": f"{self._base.calc_growth(cur_var_cost, mom_var_cost)}%",
                "本月挂号人次": cur_visits
            }
        return dept_details

    def calc_department_chart_data(self, target_date):
        """计算四大核心科室的收支与利润率
        Args:
            target_date: datetime 对象
        Returns:
            dict: 科室图表数据，包含 categories, revenue, cost, margin
        """
        month_df = self._base.filter_by_time(self.df, target_date)

        chart_data = {
            "categories": self._target_depts,
            "revenue": [],
            "cost": [],
            "margin": []
        }

        for dept in self._target_depts:
            dept_df = self._base.filter_by_department(month_df, dept)

            rev_yuan = dept_df[dept_df['大类'] == '收入']['值'].sum()
            cost_yuan = dept_df[dept_df['大类'] == '成本']['值'].sum()

            rev_wan = round(rev_yuan / 10000, 1)
            cost_wan = round(cost_yuan / 10000, 1)
            margin = self._base.safe_margin(rev_yuan, cost_yuan)

            chart_data["revenue"].append(rev_wan)
            chart_data["cost"].append(cost_wan)
            chart_data["margin"].append(margin)

        return chart_data

    def calc_department_scorecards(self, target_date):
        """生成科室专属绩效卡片数据列表
        Args:
            target_date: datetime 对象
        Returns:
            list: 科室绩效卡片数据列表
        """
        yoy_date = target_date - relativedelta(years=1)
        mom_date = target_date - relativedelta(months=1)

        cur_df = self._base.filter_by_time(self.df, target_date)
        yoy_df = self._base.filter_by_time(self.df, yoy_date)
        mom_df = self._base.filter_by_time(self.df, mom_date)

        scorecards = []

        for dept in self._target_depts:
            cur_dept_df = self._base.filter_by_department(cur_df, dept)
            yoy_dept_df = self._base.filter_by_department(yoy_df, dept)
            mom_dept_df = self._base.filter_by_department(mom_df, dept)

            cur_rev = cur_dept_df[cur_dept_df['大类'] == '收入']['值'].sum()
            cur_cost = cur_dept_df[cur_dept_df['大类'] == '成本']['值'].sum()
            cur_visits = cur_dept_df[(cur_dept_df['大类'] == '人次') & (cur_dept_df['项目'] == '挂号人次')]['值'].sum()

            yoy_rev = yoy_dept_df[yoy_dept_df['大类'] == '收入']['值'].sum()
            yoy_cost = yoy_dept_df[yoy_dept_df['大类'] == '成本']['值'].sum()
            yoy_visits = yoy_dept_df[(yoy_dept_df['大类'] == '人次') & (yoy_dept_df['项目'] == '挂号人次')]['值'].sum()

            mom_rev = mom_dept_df[mom_dept_df['大类'] == '收入']['值'].sum()
            mom_cost = mom_dept_df[mom_dept_df['大类'] == '成本']['值'].sum()
            mom_visits = mom_dept_df[(mom_dept_df['大类'] == '人次') & (mom_dept_df['项目'] == '挂号人次')]['值'].sum()

            avg_revenue = round(cur_rev / cur_visits, 0) if cur_visits > 0 else 0

            cost_structure = []
            if cur_cost > 0:
                dept_costs = cur_dept_df[cur_dept_df['大类'] == '成本']
                grouped_cost = dept_costs.groupby('二级分类')['值'].sum().sort_values(ascending=False)

                for category, value in grouped_cost.items():
                    short_name = str(category).replace("运营", "")
                    ratio = round((value / cur_cost) * 100, 1)
                    cost_structure.append({"name": short_name, "ratio": ratio})

            cost_structure_top3 = cost_structure[:3]
            margin = self._base.safe_margin(cur_rev, cur_cost)
            cost_ratio = self._base.safe_cost_ratio(cur_cost, cur_rev)

            scorecards.append({
                "name": dept,
                "revenue": round(cur_rev / 10000, 1),
                "rev_yoy": self._base.calc_growth(cur_rev, yoy_rev),
                "rev_mom": self._base.calc_growth(cur_rev, mom_rev),
                "visits": int(cur_visits),
                "visits_yoy": self._base.calc_growth(cur_visits, yoy_visits),
                "visits_mom": self._base.calc_growth(cur_visits, mom_visits),
                "avg_revenue": avg_revenue,
                "cost": round(cur_cost / 10000, 1),
                "cost_yoy": self._base.calc_growth(cur_cost, yoy_cost),
                "cost_mom": self._base.calc_growth(cur_cost, mom_cost),
                "cost_structure": cost_structure_top3,
                "margin": margin,
                "cost_ratio": cost_ratio
            })

        return scorecards

    def generate_department_data(self, target_month: str) -> dict:
        """生成科室相关所有数据
        Args:
            target_month: 目标月份，格式 "YYYY-MM"
        Returns:
            dict: 包含 department_details, department_chart_data, department_scorecards
        """
        from datetime import datetime
        target_date = datetime.strptime(target_month, '%Y-%m')
        mom_date = target_date - relativedelta(months=1)

        return {
            "department_details": self.calc_department_details(target_date, mom_date),
            "department_chart_data": self.calc_department_chart_data(target_date),
            "department_scorecards": self.calc_department_scorecards(target_date)
        }