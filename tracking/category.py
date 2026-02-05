from enum import Enum


class Category(str, Enum):
    CONNECTIVITY = "CONNECTIVITY"
    PERFORMANCE = "PERFORMANCE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    APPLICATION = "APPLICATION"
    SECURITY = "SECURITY"


def is_valid_category(value) -> bool:
    try:
        Category(value)
        return True
    except ValueError:
        return False
