class NoDataFoundException(Exception):
    """
    This exception will be raised when no data is found in the system
    """
    pass

class UnauthorizedRequestException(Exception):
    """
    The exception to be thrown when a request hits the follower directly
    """
    pass