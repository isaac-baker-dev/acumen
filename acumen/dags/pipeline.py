"""
Acumen DAG Pipeline - Python interface to the Rust/Go engine.
Falls back to in-process execution if the engine isn't running.
"""
import json
import requests
from datetime import datetime
from acumen.core.config import DAG_ENGINE_HOST, DAG_ENGINE_PORT
from acumen.core.logger import get_logger
from acumen.memory import MemoryManager

logger = get_logger("acumen.dags")


def submit_pipeline(name: str, tasks: list[dict]) -> str:
    """Submit a pipeline to the DAG engine."""
    pipeline_id = f"pipe_{datetime.now():%Y%m%d_%H%M%S}"

    try:
        resp = requests.post(
            f"http://{DAG_ENGINE_HOST}:{DAG_ENGINE_PORT}/schedule",
            json={"tasks": tasks},
            timeout=2,
        )
        if resp.ok:
            data = resp.json()
            logger.info(
                f"Pipeline submitted to scheduler: {data.get('pipeline_id', pipeline_id)}"
            )
            logger.info(f"Execution order: {data.get('execution_order', [])}")
    except requests.ConnectionError:
        logger.info("DAG engine not running. Using in-process fallback.")

    memory = MemoryManager()
    for task in tasks:
        logger.info(f"Executing task: {task['agent']}")
        from acumen.agents import crews

        crew_map = {
            "research": crews.research_crew,
            "strategist": crews.research_crew,
            "engineer": crews.coding_crew,
            "coding": crews.coding_crew,
            "debugger": crews.coding_crew,
            "knowledge": crews.learning_crew,
            "learning": crews.learning_crew,
            "security": crews.security_crew,
            "automator": crews.automation_crew,
            "automation": crews.automation_crew,
            "full_build": crews.full_build_crew,
        }

        crew_fn = crew_map.get(task["agent"])
        if not crew_fn:
            crew_fn = getattr(crews, f"{task['agent']}_crew", None)

        if crew_fn:
            try:
                result = crew_fn(task["payload"]).kickoff()
                memory.save_episode("dag_task", str(result)[:1000],
                    {"pipeline": name, "task": task["name"]})
                logger.info(f"Task completed: {task['name']}")

                try:
                    requests.post(
                        f"http://{DAG_ENGINE_HOST}:{DAG_ENGINE_PORT}/mark",
                        json={"task_id": task.get("id", task["name"]), "status": "completed"},
                        timeout=2,
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Task failed: {task['name']} - {e}")
                try:
                    requests.post(
                        f"http://{DAG_ENGINE_HOST}:{DAG_ENGINE_PORT}/mark",
                        json={"task_id": task.get("id", task["name"]), "status": "failed"},
                        timeout=2,
                    )
                except Exception:
                    pass
        else:
            logger.warning(f"No crew found for agent: {task['agent']}")

    return pipeline_id