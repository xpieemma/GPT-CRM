from fastapi import BackgroundTasks
from typing import Dict, Any, Optional
import uuid
import time
from app.utils.logging import logger

class TaskDispatcher:
    """
    Task dispatcher with process-local storage.
    
    WARNING: Task status is stored in memory and NOT shared across
    multiple Uvicorn workers. If you run with --workers 4, task status
    lookup only works if request hits same worker that created the task.
    
    Production solution: Use Celery + Redis for distributed task tracking.
    """
    
    def __init__(self):
        self._tasks = {}  # process-local only!
    
    def dispatch(self, task_type: str, payload: Dict[str, Any], 
                background_tasks: BackgroundTasks) -> str:
        """Dispatch task to background worker"""
        task_id = str(uuid.uuid4())
        
        self._tasks[task_id] = {
            "status": "pending",
            "task_type": task_type,
            "created_at": time.time(),
            "payload": payload
        }
        
        if task_type == "generate_outreach":
            background_tasks.add_task(
                self._generate_handler,
                task_id,
                payload
            )
        else:
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = f"Unknown task type: {task_type}"
        
        return task_id
    
    async def _generate_handler(self, task_id: str, payload: Dict):
        """Handle outreach generation"""
        self._tasks[task_id]["status"] = "running"
        
        try:
            from app.outreach_agent import outreach_agent
            from app.models import ConversationContext
            
            context = ConversationContext(**payload['context'])
            result = await outreach_agent.generate_response(
                context,
                tenant_id=payload['tenant_id']
            )
            
            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["result"] = result.dict()
            self._tasks[task_id]["completed_at"] = time.time()
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = str(e)
    
    def get_status(self, task_id: str) -> Optional[Dict]:
        """Get task status (process-local only)"""
        task = self._tasks.get(task_id)
        if task:
            return {
                "task_id": task_id,
                "status": task["status"],
                "result": task.get("result"),
                "error": task.get("error")
            }
        return None

# Singleton
dispatcher = TaskDispatcher()
