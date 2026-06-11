import httpx
import tomli
from pathlib import Path
from typing import Dict, Any, Optional
from clients import create_client, LLMClient
from clients.debug import debug


class LLMManager:
    """Verwaltet LLM-Instanzen für verschiedene Steps basierend auf model_config.toml."""
    
    def __init__(self, config: dict, model_config_path: str = "model_config.toml", verbose: int = 0):
        self.config = config
        self.model_config_path = Path(model_config_path)
        self.model_config: Dict[str, Any] = {}
        self.step_clients: Dict[int, LLMClient] = {}
        self.client_instances: Dict[str, LLMClient] = {}
        self.verbose = verbose  # step -> client
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
    
    def get_prompt_file_path(self, step: int) -> Optional[Path]:
        """Get prompt file path for a step from [prompts] section."""
        if not self.model_config:
            self.load_model_config()
        
        prompts_section = self.model_config.get("prompts", {})
        if not prompts_section:
            debug(1, self.verbose, f"[WARN] No [prompts] section in model_config.toml")
            return None
        
        key = f"step{step}_file"
        prompt_file = prompts_section.get(key)
        
        if not prompt_file:
            debug(1, self.verbose, f"[WARN] No '{key}' in [prompts] section")
            return None
        
        # Resolve relative path from model_config.toml location
        prompt_path = (self.model_config_path.parent / prompt_file).resolve()
        
        if not prompt_path.exists():
            debug(1, self.verbose, f"[WARN] Prompt file not found: {prompt_path}")
            return None
        
        debug(2, self.verbose, f"Prompt file for step {step}: {prompt_path}")
        return prompt_path
    
    def _create_client_for_config(self, cfg_section: Dict[str, Any], provider: str, cfg_name: str = "") -> LLMClient:
        """Create a client based on config section."""
        model = cfg_section.get("model", "")
        if not model:
            raise ValueError(f"No model specified in config: {cfg_section}")
        
        client = create_client(provider, model, self.config, verbose=self.verbose)
        
        # Set context_size_by_load from TOML config
        client.context_size_by_load = cfg_section.get("CONTEXT_SIZE_BY_MODEL_LOAD", False)
        
        # NUR explizit laden wenn CONTEXT_SIZE_BY_MODEL_LOAD=true
        # Implizit: Server lädt bei Bedarf
        context_size = cfg_section.get("context_size")
        
        if client.context_size_by_load and provider == "lmstudio" and context_size:
            debug(self.verbose, 2, f"Explicitly loading model '{model}' with context_size={context_size}")
            try:
                client.load_model(int(context_size))
            except httpx.ConnectError:
                print(f"[ERROR] Cannot connect to {provider} at {client.url}")
                print(f"[HELP] Start {provider} and check the URL in your .env file.")
                print(f"[HELP] Also verify the server is running and accepting connections.")
                exit(1)
            except Exception as e:
                print(f"[ERROR] Failed to load model '{model}' on {provider}: {e}")
                print(f"[HELP] Check the model name in model_config.toml and ensure it exists on the server.")
                exit(1)
            client._was_explicitly_loaded = True
            debug(self.verbose, 2, f"Model '{model}' loaded, instance_id={client._instance_id}")
        
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
        
        client = create_client(provider, model, self.config, verbose=self.verbose)
        
        # Legacy: CONTEXT_SIZE_BY_MODEL_LOAD aus ENV
        if provider == "lmstudio" and self.config.get("CONTEXT_SIZE_BY_MODEL_LOAD"):
            context_size = self.config.get("LMSTUDIO_CONTEXT_SIZE")
            if context_size:
                try:
                    client.load_model(int(context_size))
                except httpx.ConnectError:
                    print(f"[ERROR] Cannot connect to {provider} at {client.url}")
                    print(f"[HELP] Start {provider} and check the URL in your .env file.")
                    exit(1)
                except Exception as e:
                    print(f"[ERROR] Failed to load model on {provider}: {e}")
                    exit(1)
                client._was_explicitly_loaded = True
        
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
        """Entlädt Step 1 Client NUR wenn er explizit geladen wurde."""
        client = self.step_clients.get(1)
        if not client:
            return
        
        # NUR entladen wenn Modell explizit geladen wurde
        if not getattr(client, '_was_explicitly_loaded', False):
            debug(self.verbose, 2, f"Step 1 model '{client.model}' loaded implicitly, not unloading")
            return
        
        # Wirklich entladen (nur wenn explizit geladen)
        if self.step_clients.get(1) != self.step_clients.get(2):
            debug(self.verbose, 2, f"Explicitly unloading Step 1 model '{client.model}'")
            client.close()
            # Remove from instances if it's a unique config
            for cfg_name, inst in list(self.client_instances.items()):
                if inst == client:
                    del self.client_instances[cfg_name]
                    break
            self.step_clients[1] = None
    
    def close_all(self):
        """Schließt alle Clients die explizit geladen wurden."""
        for cfg_name, client in list(self.client_instances.items()):
            if client and getattr(client, '_was_explicitly_loaded', False):
                debug(self.verbose, 2, f"Explicitly unloading model '{client.model}'")
                client.close()
        
        # Clear all references
        self.client_instances.clear()
        self.step_clients.clear()