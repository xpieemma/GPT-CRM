from app.services.repository import repo
from typing import Optional, Dict

class PromptStore:
    """Prompt versioning and management"""
    
    def get_active_prompt(self, tenant_id: str = "default") -> Optional[Dict]:
        """Get active prompt for tenant"""
        return repo.get_active_prompt(tenant_id)
    
    def create_prompt(self, tenant_id: str, version: str, content: str, 
                     active: bool = False, description: str = ""):
        """Create new prompt version"""
        return repo.create_prompt(
            tenant_id=tenant_id,
            version=version,
            content=content,
            active=active,
            metadata={"description": description}
        )

# Singleton
prompt_store = PromptStore()
