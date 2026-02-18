from tracking.state.network_state import NetworkState


# Defines valid state transitions
VALID_TRANSITIONS = {
    NetworkState.UP: {
        NetworkState.DEGRADED,
        NetworkState.DOWN,
    },

    NetworkState.DEGRADED: {
        NetworkState.UP,
        NetworkState.DOWN,
    },

    NetworkState.DOWN: {
        NetworkState.RECOVERING,
        NetworkState.UP,
    },

    NetworkState.RECOVERING: {
        NetworkState.UP,
        NetworkState.DEGRADED,
    },
}


def is_valid_transition(current_state: NetworkState, new_state: NetworkState) -> bool:
    """
    Checks if transition between states is allowed.
    """

    if current_state == new_state:
        return True

    return new_state in VALID_TRANSITIONS.get(current_state, set())
