class EventState:
    """
    Keeps memory of previous snapshot values
    so we can detect transitions.
    """

    def __init__(self):
        self.network_id = None
        self.verdict = None
        self.online = None

    def update(self, snapshot):
        self.network_id = snapshot.get("network_id")
        self.verdict = snapshot.get("verdict")
        self.online = snapshot.get("online")
