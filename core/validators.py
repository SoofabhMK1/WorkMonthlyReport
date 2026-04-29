# 文件：core/validators.py
# 数据校验层 - Schema 校验、KPI 结果校验
import pandas as pd
from core.schema import DEFAULT_SCHEMA

class DataSchemaValidator:
    """数据源 Schema 校验器"""

    def __init__(self, config_schema=None):
        self._schema = config_schema if config_schema else DEFAULT_SCHEMA

    def validate(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        """校验 DataFrame 是否符合 Schema 要求
        Args:
            df: pandas DataFrame
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        required_columns = [
            self._schema['date_column'],
            self._schema['category_column'],
            self._schema['value_column']
        ]

        for col in required_columns:
            if col not in df.columns:
                errors.append(f"缺少必需列：'{col}'")

        return (len(errors) == 0, errors)

    def validate_and_raise(self, df: pd.DataFrame):
        """校验 DataFrame，不通过则抛出明确异常
        Args:
            df: pandas DataFrame
        Raises:
            DataSchemaError: 当校验失败时
        """
        is_valid, errors = self.validate(df)
        if not is_valid:
            raise DataSchemaError(f"数据源校验失败：{'；'.join(errors)}")


class KPIResultValidator:
    """KPI 结果校验器 - 数值合理性检查"""

    @staticmethod
    def validate_kpi_value(key: str, kpi: dict):
        """校验单个 KPI 值的合理性
        Args:
            key: KPI 名称
            kpi: KPI 数据，格式 {"value": ..., "yoy": ..., "mom": ...}
        Raises:
            KPIValueError: 当数值不合理时
        """
        value = kpi.get('value', 0)
        yoy = kpi.get('yoy', 0)
        mom = kpi.get('mom', 0)

        if 'cost' not in key.lower() and value < 0:
            raise KPIValueError(f"指标 '{key}' 的 value 不应为负数：{value}")

        if not isinstance(yoy, (int, float)) or not isinstance(mom, (int, float)):
            raise KPIValueError(f"指标 '{key}' 的 yoy/mom 必须为数值类型")

        if abs(yoy) > 1000 or abs(mom) > 1000:
            raise KPIValueError(f"指标 '{key}' 的 yoy 或 mom 异常大（超过1000%），请检查数据：yoy={yoy}%, mom={mom}%")

    @staticmethod
    def validate_department_margin(dept_name: str, margin: float):
        """校验科室利润率的合理性
        Args:
            dept_name: 科室名称
            margin: 利润率
        Raises:
            KPIValueError: 当利润率超范围时
        """
        if margin < -100 or margin > 100:
            raise KPIValueError(f"科室 '{dept_name}' 利润率异常：{margin}%，超出合理范围 [-100%, 100%]")

    @staticmethod
    def validate_department_scorecard(dept_card: dict):
        """校验科室绩效卡片的数值合理性
        Args:
            dept_card: 科室绩效卡片数据
        """
        if dept_card['revenue'] < 0:
            raise KPIValueError(f"科室 '{dept_card['name']}' 收入为负数：{dept_card['revenue']}")

        if dept_card['cost'] < 0:
            raise KPIValueError(f"科室 '{dept_card['name']}' 成本为负数：{dept_card['cost']}")

        if dept_card['cost_ratio'] < 0 or dept_card['cost_ratio'] > 100:
            raise KPIValueError(f"科室 '{dept_card['name']}' 成本率异常：{dept_card['cost_ratio']}%")

        KPIResultValidator.validate_department_margin(dept_card['name'], dept_card['margin'])

    @staticmethod
    def validate_report_data(report_data: dict):
        """校验完整报告数据的合理性
        Args:
            report_data: 完整的报告数据
        Raises:
            KPIValueError: 当数据不合理时
        """
        if 'kpis' in report_data:
            for key, kpi in report_data['kpis'].items():
                KPIResultValidator.validate_kpi_value(key, kpi)

        if 'department_scorecards' in report_data:
            for card in report_data['department_scorecards']:
                KPIResultValidator.validate_department_scorecard(card)


class DataSchemaError(Exception):
    """数据源 Schema 校验异常"""
    pass


class KPIValueError(Exception):
    """KPI 数值合理性校验异常"""
    pass