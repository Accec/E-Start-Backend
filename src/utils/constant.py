from enum import IntEnum

class UserStatus(IntEnum):
    INACTIVE = -1
    ACTIVE = 0

class LogLevel(IntEnum):
    HIGH = 3
    MIDIUM = 2
    LOW = 1

TASK_LOGGER = 'Task'
JOB_LOGGER = 'Job'
SERVER_LOGGER = 'Server'
API_LOGGER = 'API'
SCHEDULER_LOGGER = 'Scheduler'

HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_ACCEPTED = 202
HTTP_STATUS_NO_CONTENT = 204
HTTP_STATUS_INVALID_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_SERVER_ERROR = 500

EMAIL_VERCODE = "auth:email_auth:vercode:{}"
WEB3_VERCODE = "auth:web3_auth:vercode:{}"
REQUEST_RATE_LIMIT = "request:ratelimit:{}:{}"
USER_PERMISSIONS_KEY = "auth:user_permissions:{}"
ENDPOINT_PERMISSIONS_KEY = "auth:endpoint_permissions:{}:{}"

ROLE_ADMIN = "Admin"
ROLE_USER = "User"

TASK_DEMO = "demo"