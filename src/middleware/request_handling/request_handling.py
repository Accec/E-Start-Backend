
from utils.logger import Logger
from utils.error import RequestException

Logging = Logger()
async def request_handling(request):
    
    request_id = request.id
    request.ctx.request_id = request_id
    request.ctx.real_ip = request.remote_addr or request.ip
    request.ctx.ua = request.headers.get('user-agent')

    request_params = {}

    try:
        request_method = request.method

        if request_method == 'GET':
            request_params = request.args
        else:
            if 'application/json' in request.content_type: #json
                request_params = request.json
            else:
                request_params = {key: request.form.get(key) for key in request.form.keys()}

        if request_params != {}:
            Logging.info(f"request_id[{request_id}]-client_ip[{request.ip}]-url[{request.url}]-body[{request_params}]")
        

    except Exception as e:
        raise RequestException(e.__str__())