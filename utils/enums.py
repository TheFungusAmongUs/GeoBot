from enum import Enum


class QuestionStatus(Enum):

    IN_REVIEW = 0
    DENIED = -2
    APPROVED = 2
    DUPLICATE = -1
