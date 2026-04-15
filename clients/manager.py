from typing import Dict, Any, Optional
from clients import create_client, LLMClient


class LLMManager:
    """Verwaltet LLM-Instanzen für verschiedene Steps."""
    
    def __init__(self, config: dict):
        self.config = config
        self.default_client: Optional[LLMClient] = None
        self.step1_client: Optional[LLMClient] = None
    
    def init_clients(self, provider: str):
        """Initialisiert Clients basierend auf MULTIPHASE_MODE."""
        
        # Default-Client für Step 2+3
        if provider == "ollama":
            default_model = self.config.get("OLLAMA_MODEL")
        else:
            default_model = self.config.get("LMSTUDIO_MODEL")
        
        self.default_client = create_client(provider, default_model, self.config)
        
        # Step 1 Client (nur wenn unterschiedlich)
        step1_model = self.config.get("MULTIPHASE_MODEL_STEP1_OCR", "")
        
        if step1_model and step1_model != default_model:
            # Separates Modell für Step 1
            self.step1_client = create_client(provider, step1_model, self.config)
        else:
            # Wiederverwendung des default_client
            self.step1_client = self.default_client
    
    def get_client(self, step: int) -> LLMClient:
        """Gibt passenden Client für Step zurück."""
        if step == 1:
            return self.step1_client or self.default_client
        else:
            return self.default_client
    
    def cleanup_after_step1(self):
        """Entlädt step1_client nach Step 1 falls != default_client."""
        if self.step1_client and self.step1_client != self.default_client:
            self.step1_client.close()
            self.step1_client = None
    
    def close_all(self):
        """Schließt alle Clients."""
        if self.default_client:
            self.default_client.close()
        if self.step1_client and self.step1_client != self.default_client:
            self.step1_client.close()
