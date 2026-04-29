# 文件：core/data_loader.py
import pandas as pd
from pathlib import Path
from core.validators import DataSchemaValidator

class ExcelDataLoader:
    def __init__(self, file_path="data/数据.xlsx", schema=None, validate=True):
        """初始化加载器，支持相对或绝对路径
        Args:
            file_path: 数据文件路径
            schema: 数据源映射配置，默认为None使用config.yaml配置
            validate: 是否进行Schema校验，默认为True
        """
        self.file_path = Path(file_path)
        self._schema = schema
        self._validate = validate

    @property
    def schema(self):
        """获取数据源映射配置"""
        if self._schema is not None:
            return self._schema
        from core.config import config
        return {
            'date_column': config.data_schema.get('date_column', '日期'),
            'category_column': config.data_schema.get('category_column', '大类'),
            'sub_category_column': config.data_schema.get('sub_category_column', '二级分类'),
            'item_column': config.data_schema.get('item_column', '项目'),
            'department_column': config.data_schema.get('department_column', '科室'),
            'value_column': config.data_schema.get('value_column', '值'),
        }

    def load(self) -> pd.DataFrame:
        """读取数据并进行基础清洗和校验"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到数据文件：{self.file_path.absolute()}")

        print(f"正在读取数据源: {self.file_path} ...")
        df = pd.read_excel(self.file_path)

        if self._validate:
            validator = DataSchemaValidator(self.schema)
            validator.validate_and_raise(df)

        schema = self.schema
        df['日期'] = pd.to_datetime(df[schema['date_column']])
        df['值'] = pd.to_numeric(df[schema['value_column']], errors='coerce').fillna(0)

        return df