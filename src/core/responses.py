from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResponseSpec:
    code: int
    msg: str


RequestError = ResponseSpec(-1000, "Request error")
RequestTimeoutError = ResponseSpec(-1001, "Request timed out")
InvalidArgumentsError = ResponseSpec(-1002, "Invalid or missing arguments")
TokenExpiredError = ResponseSpec(-1003, "Token expired")
TooManyRequestsError = ResponseSpec(-1004, "Too many requests")
PermissionDeniedError = ResponseSpec(-1005, "Permission denied")
UserAlreadyExistsError = ResponseSpec(-1006, "The account already exists")
InvalidCredentialsError = ResponseSpec(-1007, "The account or password is invalid")
ServiceUnavailableError = ResponseSpec(-1008, "Service unavailable")
Success = ResponseSpec(0, "Success")
