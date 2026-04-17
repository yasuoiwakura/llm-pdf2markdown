import tomli
from pathlib import Path
from typing import Dict, Any, Optional
from clients import create_client, LLMClient


class LLMManager:
    """Verwaltet LLM-Instanzen für verschiedene Steps basierend auf model_config.toml."""
    
    def __init__(self, config: dict, model_config_path: str = "model_config.toml"):
        self.config = config
        self.model_config_path = Path(model_config_path)
        self.model_config: Dict[str, Any] = {}
        self.step_clients: Dict[int, LLMClient] = {}  # step -> client
        self.client_instances: Dict[str, LLMClient] = {}  # cfg_name -> client instance
    
    def load_model_config(self):
        """Load model_config.toml."""
        if not self.model_config_path.exists():
            print(f"[WARN] model_config.toml not found at {self.model_config_path}")
            return
        
        with open(self.model_config_path, "rb") as f:
            self.model_config = tomli.load(f)
        
        print(f"[OK] Loaded model config from {self.model_config_path}")
    
    def _get_step_config(self, step: int) -> Dict[str, Any]:
        """Get config section name for a step."""
        step_map = {1: "step1_cfg", 2: "step2_cfg", 3: "step3_cfg"}
        key = step_map.get(step, "step1_cfg")
        
        cfg_name = self.model_config.get(key, "step1")
        return self.model_config.get(cfg_name, {})
    
    def _create_client_for_config(self, cfg_section: Dict[str, Any], provider: str) -> LLMClient:
        """Create a client based on config section."""
        model = cfg_section.get("model", "")
        if not model:
            raise ValueError(f"No model specified in config: {cfg_section}")
        
        client = create_client(provider, model, self.config)
        
        # Load model with context_size if specified
        context_size = cfg_section.get("context_size")
        if context_size and provider == "lmstudio":
            client.load_model(int(context_size))
            print(f"[OK] Loaded model with context_size: {context_size}")
        
        return client
    
    def init_clients(self, provider: str):
        """Initialisiert Clients basierend auf model_config.toml."""
        self.load_model_config()
        
        if not self.model_config:
            print("[WARN] No model config loaded, falling back to .env config")
            self._init_clients_fallback(provider)
            return
        
        # Determine which configs are needed
        step1_cfg = self.model_config.get("step1_cfg", "step1")
        step2_cfg = self.model_config.get("step2_cfg", "step1")
        step3_cfg = self.model_config.get("step3_cfg", "step1")
        
        # Create unique client instances for each unique config
        unique_cfgs = {step1_cfg, step2_cfg, step3_cfg}
        
        for cfg_name in unique_cfgs:
            cfg_section = self.model_config.get(cfg_name, {})
            if cfg_section:
                client = self._create_client_for_config(cfg_section, provider)
                self.client_instances[cfg_name] = client
                print(f"[OK] Created client for config '{cfg_name}': {cfg_section.get('model')}")
        
        # Map steps to clients
        self.step_clients[1] = self.client_instances.get(step1_cfg)
        self.step_clients[2] = self.client_instances.get(step2_cfg)
        self.step_clients[3] = self.client_instances.get(step3_cfg)
    
    def _init_clients_fallback(self, provider: str):
        """Fallback init using .env config (legacy behavior)."""
        if provider == "ollama":
            model = self.config.get("OLLAMA_MODEL")
        else:
            model = self.config.get("LMSTUDIO_MODEL")
        
        client = create_client(provider, model, self.config)
        
        if provider == "lmstudio" and self.config.get("CONTEXT_SIZE_BY_MODEL_LOAD"):
            context_size = self.config.get("LMSTUDIO_CONTEXT_SIZE")
            if context_size:
                client.load_model(int(context_size))
        
        self.step_clients = {1: client, 2: client, 3: client}
        self.client_instances = {"default": client}
    
    def get_client(self, step: int) -> Optional[LLMClient]:
        """Gibt passenden Client für Step zurück."""
        return self.step_clients.get(step)
    
    @property
    def default_client(self) -> Optional[LLMClient]:
        """Legacy property - returns step 2+3 client."""
        return self.step_clients.get(2)
    
    @property
    def step1_client(self) -> Optional[LLMClient]:
        """Legacy property - returns step 1 client."""
        return self.step_clients.get(1)
    
    def cleanup_after_step1(self):
        """Entlädt Step 1 Client falls nicht von Step 2+3 wiederverwendet."""
        if self.step_clients.get(1) != self.step_clients.get(2):
            client = self.step_clients.get(1)
            if client:
                client.close()
                # Remove from instances if it's a unique config
                for cfg_name, inst in list(self.client_instances.items()):
                    if inst == client:
                        del self.client_instances[cfg_name]
                        break
                self.step_clients[1] = None
    
    def close_all(self):
        """Schließt alle Clients."""
        for client in self.client_instances.values():
            if client:
                client.close()
        self.client_instances.clear()
        self.step_clients.clear()