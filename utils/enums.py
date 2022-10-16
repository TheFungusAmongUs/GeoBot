from enum import Enum


class PostStatus(Enum):

    IN_REVIEW = 0
    DENIED = -2
    APPROVED = 2
    DUPLICATE = -1


class PostType(Enum):

    FEEDBACK_QUESTION = "IAF_CHANNEL_ID"
    BUG_REPORT = "BUG_REPORT_CHANNEL_ID"


class TicketStatus(Enum):
    CLOSED = -1
    OPEN = 0
    RESOLVED = 1
