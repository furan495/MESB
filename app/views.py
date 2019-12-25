import os
import json
import time
import datetime
from app.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@csrf_exempt
def querySelect(request):
    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order':
        selectList = {'orderType': list(
            map(lambda obj: obj.name, OrderType.objects.all()))}
    if params['model'] == 'user':
        roles = Role.objects.all()
        departments = Department.objects.all()
        selectList = {'gender': ['男', '女'],
                      'role': list(map(lambda obj: obj.name, roles)), 'department': list(map(lambda obj: obj.name, departments))}
    return JsonResponse({'res': selectList})


@csrf_exempt
def queryWIP(request):
    params = json.loads(request.body)
    workOrder = WorkOrder.objects.get(number=params['val'])
    events = list(map(lambda obj: '%s/%s' %
                      (obj.title, obj.time), workOrder.events.all()))
    return JsonResponse({'res': events})


@csrf_exempt
def orderSplit(request):
    params = json.loads(request.body)
    orderDesc = params['description'].split(';')
    order = Order.objects.get(key=params['key'])
    order.status = OrderStatus.objects.get(key=2)
    order.save()
    for description in orderDesc:
        if len(description.split(',')) > 1:
            for desc in range(int(description.split(',')[-1].split(':')[1])):
                workOrder = WorkOrder()
                workOrder.order = Order.objects.get(key=params['key'])
                workOrder.route = ProcessRoute.objects.get(key=1)
                workOrder.bottle = ''
                workOrder.endTime = ''
                workOrder.startTime = ''
                workOrder.number = str(time.time()*1000)
                workOrder.status = WorkOrderStatus.objects.get(key=1)
                workOrder.description = ','.join(description.split(',')[:4])
                workOrder.save()
    return JsonResponse({'res': 'succ'})
