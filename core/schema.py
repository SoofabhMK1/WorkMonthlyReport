# 文件：core/schema.py
# 数据源列名映射配置 - 支持外部配置化

DEFAULT_SCHEMA = {
    "date_column": "日期",
    "category_column": "大类",
    "sub_category_column": "二级分类",
    "item_column": "项目",
    "department_column": "科室",
    "value_column": "值"
}

CATEGORY_MAPPING = {
    "收入": "revenue",
    "成本": "cost",
    "人次": "visits"
}

ITEM_MAPPING = {
    "挂号人次": "outpatient_visits",
    "手术台数": "surgeries",
    "新客人数": "new_patients",
    "老客人数": "old_patients"
}

def get_schema(config_dict=None):
    """获取数据源映射配置，优先使用config.yaml中的配置，否则用默认值"""
    if config_dict and 'data_schema' in config_dict:
        return config_dict['data_schema']
    return DEFAULT_SCHEMA.copy()

def get_category_mapping(config_dict=None):
    """获取大类映射配置"""
    if config_dict and 'category_mapping' in config_dict:
        return config_dict['category_mapping']
    return CATEGORY_MAPPING.copy()

def get_item_mapping(config_dict=None):
    """获取项目映射配置"""
    if config_dict and 'item_mapping' in config_dict:
        return config_dict['item_mapping']
    return ITEM_MAPPING.copy()

def get_target_departments(config_dict=None):
    """获取目标科室列表"""
    if config_dict and 'target_departments' in config_dict:
        return config_dict['target_departments']
    return ["整形外科", "美容皮肤科", "美容中医科", "口腔科"]