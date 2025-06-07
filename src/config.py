import json
from utils import resource_path



CONFIG_FILE = resource_path("config.json")

def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)