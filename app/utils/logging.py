import logging
import sys
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("gpt-crm")
api_logger = logging.getLogger("gpt-crm.api")
agent_logger = logging.getLogger("gpt-crm.agent")
webhook_logger = logging.getLogger("gpt-crm.webhook")
