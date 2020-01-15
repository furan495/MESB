import os
import json
import time
import datetime
from app.models import *
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@csrf_exempt
def wincc(request):
    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    position = {'LP': '理瓶', 'XG': '旋盖', 'SLA': '数粒A',
                'SLB': '数粒B', 'SLC': '数粒C', 'CZ': '称重', 'TB': '贴签', 'HJ': '桁架'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')

    print(params)

    if position[params[0]] == '理瓶':
        workOrder = WorkOrder.objects.filter(
            Q(description__icontains=color[params[2]], bottle='', order=Order.objects.get(number=params[3]))).order_by('createTime')[0]
        workOrder.bottle = params[1]
        workOrder.startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        workOrder.status = WorkOrderStatus.objects.get(key=2)
        workOrder.save()

    event = Event()
    event.workOrder = WorkOrder.objects.get(
        Q(bottle=params[1], order=Order.objects.get(number=params[3])))
    event.bottle = params[1]
    event.source = position[params[0]]
    event.title = '进入%s单元' % position[params[0]]
    event.save()

    return JsonResponse({'res': 'res'})


@csrf_exempt
def storeOperate(request):
    position = {'CK': '出库', 'RK': '入库'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')

    print(params)

    operate = Operate()
    operate.name = position[params[0]]
    operate.pallet = Pallet.objects.get(number=params[2])
    operate.save()

    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def queryPallet(request):
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))
    bottles = Bottle.objects.filter(
        Q(order=Order.objects.get(number=params['number'])))
    num = -int(len(bottles)/9) if len(bottles)/9 > 1 else -1
    pallets = ','.join(list(map(lambda obj: obj.position.number, list(
        Pallet.objects.filter(Q(rate__lt=0.67)))[num:])))
    print('%s,' % pallets)
    return JsonResponse({'res': '%s,' % pallets})


@csrf_exempt
def loginCheck(request):
    params = json.loads(request.body)
    user = User.objects.get(phone=params['phone'])
    res = ''
    if user.password == params['password']:
        res = {'name': user.name, 'authority': user.role.authority}
    else:
        res = 'err'
    return JsonResponse({'res': res})


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
                time.sleep(0.01)
                workOrder.number = str(time.time()*1000000)
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
        position.status = '1'
        position.save()
        pallet = Pallet()
        pallet.position = StroePosition.objects.get(number=(i+1))
        pallet.number = i+1
        pallet.save()
    return JsonResponse({'res': 'ok'})
