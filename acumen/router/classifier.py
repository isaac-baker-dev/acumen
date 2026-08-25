# File: acumen/router/classifier.py
from acumen.core.llm import get_llm
from acumen.core.config import is_cloud_available
from acumen.core.logger import get_logger

logger = get_logger("acumen.router")

class TaskRouter:
    def __init__(self):
        self.classifier = get_llm("router", temperature=0.1)

    def classify(self, task: str) -> str:
        result = self.classifier.invoke(
            "Classify difficulty as SIMPLE, MEDIUM, or COMPLEX.\n"
            "SIMPLE=basic Q&A MEDIUM=research/coding COMPLEX=multi-step\n"
            f"Task: {task}\nRespond with ONE word only."
        ).strip().upper()

        for level in ["SIMPLE","MEDIUM","COMPLEX"]:
            if level in result:
                return level.lower()
        return "medium"

    def get_model_role(self, task, force_local=False):
        d = self.classify(task)
        if d == "simple": return "fast"
        if d == "complex" and is_cloud_available() and not force_local:
            return "cloud"
        return "reasoning"