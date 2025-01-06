class CloudStatusChangedWarning(Exception):
    def __init__(self, message):
        super().__init__(message)


class PathChangedWarning(Exception):
    def __init__(self, message):
        super().__init__(message)


class SongWasUnfavoritedWarning(Exception):
    def __init__(self, message):
        super().__init__(message)
