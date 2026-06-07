from datetime import datetime

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def log(self, state, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        state["agent_logs"].append({
            "agent": self.name,
            "message": message,
            "time": timestamp
        })
        print(f"[{timestamp}] {self.name}: {message}")

    def run(self, state: dict):
        raise NotImplementedError