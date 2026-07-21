from enum import Enum

class ActivityStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    SKIPPED = "Skipped"