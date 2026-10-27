import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.pagination import PageResult
from core.responses import InvalidArgumentsError
from domains.audit.services.logs import AuditLogService
from domains.audit.records import AuditLogPage, AuditLogRecord
from domains.audit.repositories.logs import AuditLogRepository
from domains.audit.controller.logs.api import AuditLogController
from domains.audit.controller.logs.schemas import GetAuditLogQuery
from domains.operations.services.jobs import SchedulerJobService
from domains.operations.jobs import SchedulerJob, SchedulerJobUpdate
from domains.operations.controller.jobs.api import SchedulerJobsController
from domains.operations.controller.jobs.schemas import PutJobBody


class AuditLogParametersTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_repository_combines_filters_and_preserves_zero_and_empty_string(self):
        items = [object()]
        page = PageResult(items=items, total_items=7, total_pages=4, page=3, page_size=2)
        with (
            patch("domains.audit.repositories.logs.AuditLog") as model,
            patch("domains.audit.repositories.logs.paginate_query",
                  new_callable=AsyncMock, return_value=page) as paginate,
        ):
            result = await AuditLogRepository().list_logs(
                id=0, user_id=0, api="", action="login", ip="127.0.0.1", ua=None,
                level=0, update_time="2026-10-27 12:00:00", create_time=None,
                page=3, page_size=2,
            )
        model.filter.assert_called_once_with(
            id=0, user_id=0, api="", action="login", ip="127.0.0.1", level=0,
            update_time="2026-10-27 12:00:00",
        )
        model.all.assert_not_called()
        paginate.assert_awaited_once_with(model.filter.return_value, 3, 2)
        self.assertEqual(result, AuditLogPage(items=items, total_items=7, total_pages=4))

    async def test_repository_empty_filters_use_full_query_and_default_pagination(self):
        page = PageResult(items=[], total_items=0, total_pages=0, page=1, page_size=20)
        with (
            patch("domains.audit.repositories.logs.AuditLog") as model,
            patch("domains.audit.repositories.logs.paginate_query",
                  new_callable=AsyncMock, return_value=page) as paginate,
        ):
            result = await AuditLogRepository().list_logs()
        model.all.assert_called_once_with()
        model.filter.assert_not_called()
        paginate.assert_awaited_once_with(model.all.return_value, 1, 20)
        self.assertEqual(result, AuditLogPage(items=[], total_items=0, total_pages=0))

    async def test_service_forwards_explicit_query_parameters(self):
        query = GetAuditLogQuery(id=3, user_id=4, action="read", page=2, page_size=10)
        store = Mock(list_logs=AsyncMock(return_value=AuditLogPage([], 0, 0)))
        result = await AuditLogService(logs=store).list_logs(**query.model_dump())
        store.list_logs.assert_awaited_once_with(**query.model_dump())
        self.assertIs(result, store.list_logs.return_value)

    async def test_controller_maps_query_and_preserves_paginated_response(self):
        query = GetAuditLogQuery(
            id=0, user_id=2, api="/api/v1/user/dashboard", action="read", ip="127.0.0.1",
            ua="test", level=0, create_time="2026-10-27 12:00:00", page=2, page_size=5,
        )
        item = SimpleNamespace(**{key: value for key, value in query.model_dump().items()
                                  if key not in {"page", "page_size"}})
        service = Mock(list_logs=AsyncMock(return_value=AuditLogPage([item], 6, 2)))
        response = await AuditLogController(audit_service=service).list_logs(None, query)
        service.list_logs.assert_awaited_once_with(**query.model_dump())
        payload = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["total_items"], 6)
        self.assertEqual(payload["total_pages"], 2)
        self.assertEqual(payload["results"][0]["id"], 0)
        self.assertEqual(payload["results"][0]["action"], "read")

    async def test_record_contract_is_unchanged(self):
        record = AuditLogRecord(user_id=1, api="/api/v1/user/login", action="login",
                                ip="127.0.0.1", ua="test", level=0)
        store = Mock(record=AsyncMock(return_value="stored"))
        self.assertEqual(await AuditLogService(logs=store).record(record), "stored")
        store.record.assert_awaited_once_with(record)


class SchedulerJobParametersTestCase(unittest.IsolatedAsyncioTestCase):
    def make_port(self):
        return Mock(
            get_jobs=AsyncMock(return_value={
                "interval": {"job_type": "interval", "interval": 30, "cron": None, "status": 1},
                "cron": {"job_type": "cron", "interval": None, "cron": "0 * * * *", "status": 1},
            }),
            update_job=AsyncMock(return_value=True),
        )

    async def test_service_constructs_domain_update_and_preserves_zero_status(self):
        for fields in (
            {"job_name": "interval", "interval": 60, "status": 0},
            {"job_name": "cron", "cron": "30 * * * *"},
        ):
            with self.subTest(fields=fields):
                port = self.make_port()
                result = await SchedulerJobService(jobs=port).update_job(**fields)
                self.assertTrue(result)
                port.get_jobs.assert_awaited_once_with()
                port.update_job.assert_awaited_once_with(SchedulerJobUpdate(**fields))

    async def test_invalid_or_missing_job_does_not_reach_gateway_update(self):
        for fields in (
            {"job_name": "missing", "status": 0},
            {"job_name": "interval", "interval": 0},
            {"job_name": "interval", "interval": -1},
            {"job_name": "interval", "cron": "0 * * * *"},
            {"job_name": "cron", "interval": 10},
            {"job_name": "interval", "status": 2},
        ):
            with self.subTest(fields=fields):
                port = self.make_port()
                self.assertFalse(await SchedulerJobService(jobs=port).update_job(**fields))
                port.update_job.assert_not_awaited()

    async def test_service_propagates_gateway_failure(self):
        port = self.make_port()
        port.update_job.return_value = False
        self.assertFalse(await SchedulerJobService(jobs=port).update_job(job_name="interval", status=0))

    async def test_controller_maps_update_body_and_keeps_success_status(self):
        service = Mock(get_jobs=AsyncMock(return_value={"interval": object()}),
                       update_job=AsyncMock(return_value=True))
        body = PutJobBody(job_name="interval", interval=60, status=0)
        response = await SchedulerJobsController(job_service=service).update_job(None, body)
        service.update_job.assert_awaited_once_with(job_name="interval", interval=60, cron=None, status=0)
        self.assertEqual(response.status, 201)
        self.assertEqual(json.loads(response.body)["code"], 0)

    async def test_controller_keeps_bad_request_for_unknown_and_invalid_jobs(self):
        for exists in (False, True):
            with self.subTest(exists=exists):
                service = Mock(get_jobs=AsyncMock(return_value={"interval": object()} if exists else {}),
                               update_job=AsyncMock(return_value=False))
                body = PutJobBody(job_name="interval", status=2)
                response = await SchedulerJobsController(job_service=service).update_job(None, body)
                self.assertEqual(response.status, 400)
                self.assertEqual(json.loads(response.body)["code"], InvalidArgumentsError.code)
                self.assertEqual(service.update_job.await_count, int(exists))

    async def test_controller_list_response_preserves_job_mapping(self):
        job = SchedulerJob(name="interval", job_type="interval", interval=30, status=0)
        service = Mock(get_jobs=AsyncMock(return_value={"interval": job}))
        response = await SchedulerJobsController(job_service=service).list_jobs(None)
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.body)["results"], {"interval": job.to_mapping()})


if __name__ == "__main__":
    unittest.main()
