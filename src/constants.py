from enum import Enum, unique


@unique
class WorkloadOperation(str, Enum):
    """Supported workload operations"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
