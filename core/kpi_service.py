# 文件：core/kpi_service.py
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MonthlyKPIService:
    def __init__(self, dataframe: pd.DataFrame):
        """注入清洗好的数据源"""
        self.df = dataframe

    def _get_time_windows(self, target_month_str):
        """计算时间窗口（本期、环比期、同比期）"""
        target_date = datetime.strptime(target_month_str, '%Y-%m')
        return {
            'current': target_date,
            'mom': target_date - relativedelta(months=1),
            'yoy': target_date - relativedelta(years=1)
        }

    def _calc_raw_metrics(self, target_date):
        """全面扩充：计算单个月份的基础财务与业务指标"""
        month_df = self.df[
            (self.df['日期'].dt.year == target_date.year) & 
            (self.df['日期'].dt.month == target_date.month)
        ]

        if month_df.empty:
            return {
                'revenue': 0, 'total_cost': 0, 'gross_profit': 0, 'net_profit': 0, 
                'visits': 0, 'surgeries': 0, 'new_patients': 0, 'old_patients': 0
            }

        # --- 财务类 ---
        revenue = month_df[month_df['大类'] == '收入']['值'].sum()
        total_cost = month_df[month_df['大类'] == '成本']['值'].sum() # 新增：总成本
        
        variable_costs = month_df[(month_df['大类'] == '成本') & (month_df['二级分类'].str.contains('变动', na=False))]['值'].sum()
        gross_profit = revenue - variable_costs
        
        fixed_costs = month_df[(month_df['大类'] == '成本') & (~month_df['二级分类'].str.contains('变动', na=False))]['值'].sum()
        net_profit = gross_profit - fixed_costs

        # --- 业务漏斗类 ---
        visits = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '挂号人次')]['值'].sum()
        surgeries = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '手术台数')]['值'].sum() # 新增：手术台次
        new_patients = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '新客人数')]['值'].sum() # 新增：新客
        old_patients = month_df[(month_df['大类'] == '人次') & (month_df['项目'] == '老客人数')]['值'].sum() # 新增：老客

        return {
            'revenue': revenue, 'total_cost': total_cost, 'gross_profit': gross_profit, 'net_profit': net_profit, 
            'visits': visits, 'surgeries': surgeries, 'new_patients': new_patients, 'old_patients': old_patients
        }

    def _calc_growth(self, current, previous):
        """安全计算增长率"""
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return round(((current - previous) / previous) * 100, 1)
    
    def _calc_department_details(self, current_date, mom_date):
        """计算各科室的核心指标明细及环比，喂给大模型做归因分析"""
        cur_df = self.df[(self.df['日期'].dt.year == current_date.year) & (self.df['日期'].dt.month == current_date.month)]
        mom_df = self.df[(self.df['日期'].dt.year == mom_date.year) & (self.df['日期'].dt.month == mom_date.month)]

        dept_details = {}
        # 获取所有出现的科室
        departments = pd.concat([cur_df['科室'], mom_df['科室']]).dropna().unique()

        for dept in departments:
            cur_dept = cur_df[cur_df['科室'] == dept]
            mom_dept = mom_df[mom_df['科室'] == dept]

            # 计算各项当月值
            cur_rev = cur_dept[cur_dept['大类'] == '收入']['值'].sum()
            cur_var_cost = cur_dept[(cur_dept['大类'] == '成本') & (cur_dept['二级分类'].str.contains('变动', na=False))]['值'].sum()
            cur_visits = cur_dept[(cur_dept['大类'] == '人次') & (cur_dept['项目'] == '挂号人次')]['值'].sum()

            # 计算各项上月值（用于算环比）
            mom_rev = mom_dept[mom_dept['大类'] == '收入']['值'].sum()
            mom_var_cost = mom_dept[(mom_dept['大类'] == '成本') & (mom_dept['二级分类'].str.contains('变动', na=False))]['值'].sum()

            dept_details[dept] = {
                "本月收入": cur_rev,
                "收入环比": f"{self._calc_growth(cur_rev, mom_rev)}%",
                "本月变动成本(耗材等)": cur_var_cost,
                "变动成本环比": f"{self._calc_growth(cur_var_cost, mom_var_cost)}%",
                "本月挂号人次": cur_visits
            }
        return dept_details
    
    def _calc_department_chart_data(self, target_date):
        """计算四大核心科室的收支与利润率，单位转化为'万元'"""
        month_df = self.df[
            (self.df['日期'].dt.year == target_date.year) & 
            (self.df['日期'].dt.month == target_date.month)
        ]
        
        # 锁定我们需要对比的四个主力科室
        target_depts = ["整形外科", "美容皮肤科", "美容中医科", "口腔科"]
        
        chart_data = {
            "categories": target_depts,
            "revenue": [],
            "cost": [],
            "margin": []
        }
        
        for dept in target_depts:
            dept_df = month_df[month_df['科室'] == dept]
            
            # 计算真实收入与总成本 (将元转换为万元，保留1位小数)
            rev_yuan = dept_df[dept_df['大类'] == '收入']['值'].sum()
            cost_yuan = dept_df[dept_df['大类'] == '成本']['值'].sum()
            
            rev_wan = round(rev_yuan / 10000, 1)
            cost_wan = round(cost_yuan / 10000, 1)
            
            # 安全计算利润率 (防除以0报错)
            if rev_yuan > 0:
                margin = round(((rev_yuan - cost_yuan) / rev_yuan) * 100, 1)
            else:
                margin = 0.0 if cost_yuan == 0 else -100.0
                
            chart_data["revenue"].append(rev_wan)
            chart_data["cost"].append(cost_wan)
            chart_data["margin"].append(margin)
            
        return chart_data
    
    def _calc_department_scorecards(self, target_date):
        """生成科室专属绩效卡片数据列表 (包含客单价与成本结构)"""
        cur_date = target_date
        yoy_date = target_date - relativedelta(years=1)
        mom_date = target_date - relativedelta(months=1)
        
        cur_df = self.df[(self.df['日期'].dt.year == cur_date.year) & (self.df['日期'].dt.month == cur_date.month)]
        yoy_df = self.df[(self.df['日期'].dt.year == yoy_date.year) & (self.df['日期'].dt.month == yoy_date.month)]
        mom_df = self.df[(self.df['日期'].dt.year == mom_date.year) & (self.df['日期'].dt.month == mom_date.month)]

        target_depts = ["整形外科", "美容皮肤科", "美容中医科", "口腔科"]
        scorecards = []

        for dept in target_depts:
            cur_dept_df = cur_df[cur_df['科室'] == dept]
            yoy_dept_df = yoy_df[yoy_df['科室'] == dept]
            mom_dept_df = mom_df[mom_df['科室'] == dept]

            # 提取基础数据
            cur_rev = cur_dept_df[cur_dept_df['大类'] == '收入']['值'].sum()
            cur_cost = cur_dept_df[cur_dept_df['大类'] == '成本']['值'].sum()
            cur_visits = cur_dept_df[(cur_dept_df['大类'] == '人次') & (cur_dept_df['项目'] == '挂号人次')]['值'].sum()

            yoy_rev = yoy_dept_df[yoy_dept_df['大类'] == '收入']['值'].sum()
            yoy_cost = yoy_dept_df[yoy_dept_df['大类'] == '成本']['值'].sum()
            yoy_visits = yoy_dept_df[(yoy_dept_df['大类'] == '人次') & (yoy_dept_df['项目'] == '挂号人次')]['值'].sum()
            
            mom_rev = mom_dept_df[mom_dept_df['大类'] == '收入']['值'].sum()
            mom_cost = mom_dept_df[mom_dept_df['大类'] == '成本']['值'].sum()
            mom_visits = mom_dept_df[(mom_dept_df['大类'] == '人次') & (mom_dept_df['项目'] == '挂号人次')]['值'].sum()

            # --- 新增维度 1：计算客单价 ---
            avg_revenue = round(cur_rev / cur_visits, 0) if cur_visits > 0 else 0

            # --- 新增维度 2：计算成本结构 TOP3 ---
            cost_structure = []
            if cur_cost > 0:
                dept_costs = cur_dept_df[cur_dept_df['大类'] == '成本']
                grouped_cost = dept_costs.groupby('二级分类')['值'].sum().sort_values(ascending=False)
                
                for category, value in grouped_cost.items():
                    # 简化分类名，让手机端显示更清爽
                    short_name = str(category).replace("运营", "") 
                    ratio = round((value / cur_cost) * 100, 1)
                    cost_structure.append({"name": short_name, "ratio": ratio})
            
            cost_structure_top3 = cost_structure[:3]

            # 计算利润率和吃水线
            margin = round(((cur_rev - cur_cost) / cur_rev) * 100, 1) if cur_rev > 0 else 0.0
            cost_ratio = min(round((cur_cost / cur_rev) * 100, 1) if cur_rev > 0 else 100, 100)

            # 打包组装
            scorecards.append({
                "name": dept,
                "revenue": round(cur_rev / 10000, 1),
                "rev_yoy": self._calc_growth(cur_rev, yoy_rev),
                "rev_mom": self._calc_growth(cur_rev, mom_rev),
                "visits": int(cur_visits),
                "visits_yoy": self._calc_growth(cur_visits, yoy_visits),
                "visits_mom": self._calc_growth(cur_visits, mom_visits),
                "avg_revenue": avg_revenue,  # 注入客单价
                "cost": round(cur_cost / 10000, 1),
                "cost_yoy": self._calc_growth(cur_cost, yoy_cost),
                "cost_mom": self._calc_growth(cur_cost, mom_cost),
                "cost_structure": cost_structure_top3, # 注入成本结构
                "margin": margin,
                "cost_ratio": cost_ratio
            })
            
        return scorecards

    def generate_report_data(self, target_month: str) -> dict:
        """组装最终数据时，将新指标加入输出契约"""
        times = self._get_time_windows(target_month)
        cur = self._calc_raw_metrics(times['current'])
        mom = self._calc_raw_metrics(times['mom'])
        yoy = self._calc_raw_metrics(times['yoy'])

        department_details = self._calc_department_details(times['current'], times['mom'])
        department_chart_data = self._calc_department_chart_data(times['current'])
        department_scorecards = self._calc_department_scorecards(times['current'])

        return {
            "report_month": target_month,
            "kpis": {
                "total_revenue": {"value": cur['revenue'], "yoy": self._calc_growth(cur['revenue'], yoy['revenue']), "mom": self._calc_growth(cur['revenue'], mom['revenue'])},
                "total_cost": {"value": cur['total_cost'], "yoy": self._calc_growth(cur['total_cost'], yoy['total_cost']), "mom": self._calc_growth(cur['total_cost'], mom['total_cost'])},
                "gross_profit": {"value": cur['gross_profit'], "yoy": self._calc_growth(cur['gross_profit'], yoy['gross_profit']), "mom": self._calc_growth(cur['gross_profit'], mom['gross_profit'])},
                "net_profit": {"value": cur['net_profit'], "yoy": self._calc_growth(cur['net_profit'], yoy['net_profit']), "mom": self._calc_growth(cur['net_profit'], mom['net_profit'])},
                "total_visits": {"value": cur['visits'], "yoy": self._calc_growth(cur['visits'], yoy['visits']), "mom": self._calc_growth(cur['visits'], mom['visits'])},
                "surgeries": {"value": cur['surgeries'], "yoy": self._calc_growth(cur['surgeries'], yoy['surgeries']), "mom": self._calc_growth(cur['surgeries'], mom['surgeries'])},
                "new_patients": {"value": cur['new_patients'], "yoy": self._calc_growth(cur['new_patients'], yoy['new_patients']), "mom": self._calc_growth(cur['new_patients'], mom['new_patients'])},
                "old_patients": {"value": cur['old_patients'], "yoy": self._calc_growth(cur['old_patients'], yoy['old_patients']), "mom": self._calc_growth(cur['old_patients'], mom['old_patients'])}
            },
            "department_details": department_details,
            "department_chart_data": department_chart_data,
            "department_scorecards": department_scorecards
        }