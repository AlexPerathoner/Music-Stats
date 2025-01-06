class UpdateTrackError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InsertTrackError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TrackHashNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlayCountDecreasedError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InsertPlayCountError(Exception):
    def __init__(self, message):
        super().__init__(message)


class UpdatePlayCountError(Exception):
    def __init__(self, message):
        super().__init__(message)


class AutomatorError(Exception):
    def __init__(self, message):
        super().__init__(message)
