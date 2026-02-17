from enum import Enum


class EventType(str, Enum):
    INTERNET_DOWN = "INTERNET_DOWN"
    HIGH_LATENCY = "HIGH_LATENCY"
    PACKET_LOSS_SPIKE = "PACKET_LOSS_SPIKE"
    NETWORK_SWITCH = "NETWORK_SWITCH"
    ROUTER_UNREACHABLE = "ROUTER_UNREACHABLE"
    WEBSITE_UNREACHABLE = "WEBSITE_UNREACHABLE"
    DNS_FAILURE = "DNS_FAILURE"
    NETWORK_RESTORED = "NETWORK_RESTORED"
    NETWORK_STATUS_CHANGE = "NETWORK_STATUS_CHANGE"


def is_valid_event_type(value) -> bool:
    try:
        EventType(value)
        return True
    except ValueError:
        return False