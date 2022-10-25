class CantGetCoordinates(Exception):
    """Program can't get current GPS-coordinates"""


class ApiServiceError(Exception):
    """Program can't get current weather"""


class UnconfiguredVariable(Exception):
    """Environment variable is not set"""