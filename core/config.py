# 文件：core/config.py
import os
import yaml
from dotenv import load_dotenv

# 自动寻找并加载 .env 文件中的环境变量
load_dotenv()

class AppConfig:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    @property
    def llm_provider(self):
        """获取当前激活的 LLM 供应商名称"""
        return self._config['llm']['active_provider']

    @property
    def llm_settings(self):
        """获取当前激活的 LLM 具体参数"""
        provider = self.llm_provider
        return self._config['llm']['providers'][provider]

    @property
    def prompt_path(self):
        """获取提示词路径"""
        return self._config['llm']['prompt_template_path']

    def get_api_key(self):
        """根据当前激活的供应商，自动去环境变量里拿对应的 API KEY"""
        provider = self.llm_provider.upper() # 例如把 'deepseek' 变成 'DEEPSEEK'
        # 尝试获取如 DEEPSEEK_API_KEY
        return os.getenv(f"{provider}_API_KEY")

    def get_base_url(self):
        """获取 BASE URL"""
        provider = self.llm_provider.upper()
        return os.getenv(f"{provider}_BASE_URL")

# 实例化一个全局配置对象供其他模块导入使用
config = AppConfig()