import os
import yaml
from pathlib import Path

class ProviderService:
    def __init__(self, config_path: str = "configs/providers.yaml"):
        self.config_path = config_path
        self._config = None

    def _load_config(self):
        if self._config is None:
            path = Path(self.config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                self._config = {"providers": {}}
        return self._config

    def get_all_providers(self) -> dict:
        """返回所有 provider 配置"""
        config = self._load_config()
        return config.get("providers", {})

    def get_provider_config(self, name: str) -> dict | None:
        """返回单个 provider 的完整配置"""
        providers = self.get_all_providers()
        return providers.get(name)

    def get_model_limits(self, provider: str, model: str) -> dict:
        """
        返回 {"max_input_mb": float, "max_input_minutes": float}
        如果未知模型，返回保守默认值 {"max_input_mb": 20, "max_input_minutes": 10}
        """
        default_limits = {"max_input_mb": 20.0, "max_input_minutes": 10.0}
        
        provider_cfg = self.get_provider_config(provider)
        if not provider_cfg:
            return default_limits
        
        models = provider_cfg.get("models", {})
        model_cfg = models.get(model)
        
        if not model_cfg:
            return default_limits
            
        return {
            "max_input_mb": float(model_cfg.get("max_input_mb", default_limits["max_input_mb"])),
            "max_input_minutes": float(model_cfg.get("max_input_minutes", default_limits["max_input_minutes"]))
        }

    def get_optimal_chunk_params(self, provider: str, model: str, file_size_mb: float, duration_minutes: float = 0) -> dict:
        """
        核心方法！根据模型能力和文件实际大小决定是否需要切分
        返回 {"max_minutes": int, "max_mb": int, "skip_split": bool}
        当文件在模型上限内时，skip_split=True
        """
        limits = self.get_model_limits(provider, model)
        max_mb = limits["max_input_mb"]
        max_minutes = limits["max_input_minutes"]
        
        skip_split = False
        # 如果文件大小和时长都在模型限制范围内，则跳过切分
        # 如果 duration_minutes 为 0，我们只根据 file_size_mb 判断，或者假设时长也符合（如果任务没提供时长）
        if file_size_mb <= max_mb:
            if duration_minutes <= 0 or duration_minutes <= max_minutes:
                skip_split = True
        
        return {
            "max_minutes": int(max_minutes),
            "max_mb": int(max_mb),
            "skip_split": skip_split
        }

    def has_server_key(self, provider: str) -> bool:
        """检查服务端是否配置了 API key"""
        provider_cfg = self.get_provider_config(provider)
        if not provider_cfg:
            return False
        
        env_var = provider_cfg.get("api_key_env")
        if not env_var:
            return False
            
        return bool(os.environ.get(env_var))
