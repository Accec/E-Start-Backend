import sys
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic import ValidationError

from core import api_schema
from core.api_schema import (
    ArgsInvalidResponse,
    AuthorizedErrorResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginatorSettings,
    RateLimitResponse,
    RequestErrorResponse,
    Response,
    TokenExpiredResponse,
)
from core.responses import (
    InvalidArgumentsError,
    InvalidCredentialsError,
    PermissionDeniedError,
    RequestError,
    Success,
    TokenExpiredError,
    TooManyRequestsError,
    UserAlreadyExistsError,
)
from domains.identity_access.controller.roles.schemas import GetRoleQuery
from domains.identity_access.controller.auth import schemas as auth


class ResponseModelTestCase(unittest.TestCase):
    def test_response_has_one_shared_envelope(self):
        self.assertEqual(Response().model_dump(), {
            "code": Success.code,
            "msg": Success.msg,
            "results": None,
        })
        self.assertEqual(set(Response.model_fields), {"code", "msg", "results"})
        self.assertFalse(hasattr(api_schema, "SuccessResponse"))

    def test_response_serializes_object_list_and_empty_results(self):
        for results in ({"id": 1}, [{"id": 1}], [], None):
            with self.subTest(results=results):
                self.assertEqual(Response(results=results).model_dump()["results"], results)

    def test_paginated_response_inherits_envelope_and_requires_metadata(self):
        response = PaginatedResponse(results=[{"id": 1}], total_items=1, total_pages=1)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.model_dump(), {
            "code": Success.code,
            "msg": Success.msg,
            "results": [{"id": 1}],
            "total_items": 1,
            "total_pages": 1,
        })
        for values in ({}, {"total_items": 1}, {"total_pages": 1}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                PaginatedResponse(**values)

    def test_error_responses_preserve_business_defaults(self):
        cases = (
            (RequestErrorResponse, RequestError),
            (TokenExpiredResponse, TokenExpiredError),
            (AuthorizedErrorResponse, PermissionDeniedError),
            (ArgsInvalidResponse, InvalidArgumentsError),
            (RateLimitResponse, TooManyRequestsError),
            (auth.InvalidCredentialsResponse, InvalidCredentialsError),
            (auth.AccountAlreadyExistsResponse, UserAlreadyExistsError),
        )
        for model, specification in cases:
            with self.subTest(model=model.__name__):
                self.assertEqual(model().model_dump(), {
                    "code": specification.code,
                    "msg": specification.msg,
                    "results": None,
                })
        self.assertEqual(ErrorResponse(code=-1, msg="invalid", results={"field": "name"}).model_dump(), {
            "code": -1,
            "msg": "invalid",
            "results": {"field": "name"},
        })

    def test_login_token_is_validated_and_nested_under_results(self):
        response = Response(results=auth.LoginPayload(token="signed-token"))
        self.assertEqual(response.model_dump(), {
            "code": Success.code,
            "msg": Success.msg,
            "results": {"token": "signed-token"},
        })
        self.assertFalse(hasattr(auth, "PostLoginResponse"))
        for values in ({}, {"token": None}, {"token": 123}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                auth.LoginPayload(**values)

    def test_role_query_reuses_pagination_settings(self):
        self.assertTrue(issubclass(GetRoleQuery, PaginatorSettings))
        self.assertEqual(GetRoleQuery().model_dump(), {
            "page": 1,
            "page_size": 20,
            "id": None,
            "role_name": None,
        })
        query = GetRoleQuery(page=2, page_size=5, role_name="admin")
        self.assertEqual((query.page, query.page_size, query.role_name), (2, 5, "admin"))


if __name__ == "__main__":
    unittest.main()
