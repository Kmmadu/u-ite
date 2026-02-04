from datetime import datetime
from uuid import uuid4


def create_event(event_type, details):
    return {
        "id": str(uuid4()),
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
