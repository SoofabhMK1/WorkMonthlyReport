# 文件：core/data_loader.py
import pandas as pd
from pathlib import Path

class ExcelDataLoader:
    def __init__(self, file_path="data/数据.xlsx"):
        """初始化加载器，支持相对或绝对路径"""
        self.file_path = Path(file_path)

    def load(self) -> pd.DataFrame:
        """读取数据并进行基础清洗"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到数据文件：{self.file_path.absolute()}")
            
        print(f"正在读取数据源: {self.file_path} ...")
        # 读取 Excel，需要安装 openpyxl
        df = pd.read_excel(self.file_path)
        
        # 基础清洗：标准化列名和数据类型
        df['日期'] = pd.to_datetime(df['日期'])
        df['值'] = pd.to_numeric(df['值'], errors='coerce').fillna(0)
        
        return df