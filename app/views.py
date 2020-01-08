import os
import json
import time
import random
import datetime
from app.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@csrf_exempt
def wincc(request):
    try:
        print(json.loads(str(request.body, 'utf8').replace('\'', '\"')), 'ok')
    except:
        print(request.body, 'err')
    return JsonResponse({'res': 'res'})


@csrf_exempt
def querySelect(request):
    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order':
        selectList = {'orderType': list(
            map(lambda obj: obj.name, OrderType.objects.all())), 'route': list(
            map(lambda obj: [obj.name, obj.key], ProcessRoute.objects.all()))}
    if params['model'] == 'store':
        selectList = {'storeType': list(
            map(lambda obj: obj.name, StoreType.objects.all())), 'workShop': list(
            map(lambda obj: obj.name, WorkShop.objects.all()))}
    if params['model'] == 'user':
        roles = Role.objects.all()
        departments = Department.objects.all()
        selectList = {'gender': ['男', '女'],
                      'role': list(map(lambda obj: obj.name, roles)), 'department': list(map(lambda obj: obj.name, departments))}
    return JsonResponse({'res': selectList})


@csrf_exempt
def updateProcessByRoute(request):
    params = json.loads(request.body)
    Process.objects.filter(
        route=ProcessRoute.objects.get(key=params['key'])).delete()
    orders = json.loads(params['value'])['linkDataArray']
    processes = json.loads(params['value'])['nodeDataArray']

    for i in range(len(processes)):
        process = Process()
        process.route = ProcessRoute.objects.get(key=params['key'])
        if i == len(processes)-1:
            proc = list(
                filter(lambda obj: obj['key'] == orders[-1]['to'], processes))
            process.name = proc[0]['text']
        else:
            proc = list(
                filter(lambda obj: obj['key'] == orders[i]['from'], processes))
            process.name = proc[0]['text']
        process.save()
    return JsonResponse({'res': ''})


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
                workOrder.order = order
                workOrder.bottle = ''
                workOrder.endTime = ''
                workOrder.startTime = ''
                workOrder.number = str(time.time()*1000)[:12]
                workOrder.status = WorkOrderStatus.objects.get(key=1)
                workOrder.description = ','.join(description.split(',')[:4])
                workOrder.save()
    return JsonResponse({'res': 'succ'})


@csrf_exempt
def addBottle(request):
    params = json.loads(request.body)
    for count in range(params['counts']):
        bottle = Bottle()
        bottle.order = Order.objects.get(key=params['key'])
        bottle.number = ''
        bottle.color = params['color']
        bottle.red = params['red']
        bottle.green = params['green']
        bottle.blue = params['blue']
        bottle.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def createStore(request):
    params = json.loads(request.body)
    count = params['row']*params['column']
    for i in range(count):
        position = StroePosition()
        position.store = Store.objects.get(key=params['key'])
        position.number = i+1
        position.status = random.choice(['1', '2'])
        position.save()
    return JsonResponse({'res': 'ok'})
