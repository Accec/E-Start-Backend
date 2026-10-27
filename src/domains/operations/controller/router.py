from .jobs.api import register_routes as register_job_routes


def register_routes(admin_blueprint, *, job_service, jwt_auth):
    register_job_routes(admin_blueprint, job_service=job_service, jwt_auth=jwt_auth)
