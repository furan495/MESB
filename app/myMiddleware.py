from app.models import *
from django.utils.deprecation import MiddlewareMixin


class EventTrigger(MiddlewareMixin):

    def process_response(self, request, response):
        method = {'GET': '查询', 'POST': '新增', 'PUT': '修改', 'DELETE': '删除'}
        module = {'orders': '订单', 'workOrders': '工单'}
        print('XXX%s了%s' % (method[request.method],
                            module[request.path.split('/')[2]]))
        return response
