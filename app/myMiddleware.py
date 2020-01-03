import json
from app.models import *
from django.utils.deprecation import MiddlewareMixin


def selectTitle(params):
    if 'username' in json.loads(params['cookie']):
        if params['endTime']=='':
            return '开始生产'
        else:
            return '结束生产'
    else:
        return '进入某个工位'


class EventTrigger(MiddlewareMixin):

    def process_request(self, request):
        if request.method == 'GET':
            pass
        if request.method == 'POST':
            pass
        if request.method == 'PUT':
            url = request.path.split('/')
            params = json.loads(request.body)
            if url[2] == 'workOrders':
                event = Event()
                event.workOrder = WorkOrder.objects.get(key=url[3])
                event.source = json.loads(params['cookie'])[
                    'username'] if 'username' in json.loads(params['cookie']) else '某个工位'
                event.bottle = params['bottle'] if params['bottle'] else ''
                event.title = selectTitle(params)
                event.save()
        if request.method == 'DELETE':
            pass
