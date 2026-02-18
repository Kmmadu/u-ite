from enum import Enum


class NetworkState(str, Enum):
    """
    Represents the current health state of a monitored network.
    """

    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    RECOVERING = "RECOVERING"


def is_valid_network_state(value) -> bool:
    """
    Validates if the provided value is a valid NetworkState.
    """
    if isinstance(value, NetworkState):
        return True

    if isinstance(value, str):
        return value.upper() in NetworkState.__members__

    return False
