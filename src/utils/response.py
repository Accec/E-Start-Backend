
class Response(object):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

RequestError = Response(-1000, "")
TimeoutError = Response(-1001, "Time out")
ArgsInvalidError = Response(-1002, "Arg invalid or isn't specified")
TokenError = Response(-1003, "Token expied")
RateLimitError = Response(-1004, "Arg invalid or isn't specified")
AuthorizedError = Response(-1005, "Permission invalid")

Successfully = Response(0, "Successfully")