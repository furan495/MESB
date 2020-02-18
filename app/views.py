import os
import json
import time
import datetime
import numpy as np
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

    try:
        event = Event()
        event.workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], order=Order.objects.get(number=params[3])))
        event.bottle = params[1]
        event.source = position[params[0]]
        event.title = '进入%s单元' % position[params[0]]
        event.save()
    except Exception as e:
        print(e, '这里有问题')

    return JsonResponse({'res': 'res'})


@csrf_exempt
def storeOperate(request):
    position = {'CK': '出库', 'RK': '入库'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')
    workOrder = WorkOrder.objects.get(
        Q(bottle=params[1], order=Order.objects.get(number=params[3])))
    event = Event()
    event.workOrder = workOrder
    event.bottle = params[1]
    event.source = position[params[0]]
    event.title = '进入%s单元' % position[params[0]]
    event.save()
    product = Product.objects.get(workOrder=workOrder)
    pallet = Pallet.objects.filter(Q(rate__lt=0.67))[0]
    if pallet.hole1 == False:
        pallet.hole1 = True
        pallet.hole1Content = product.name
    elif pallet.hole2 == False:
        pallet.hole2 = True
        pallet.hole2Content = product.name
    elif pallet.hole3 == False:
        pallet.hole3 = True
        pallet.hole3Content = product.name
    elif pallet.hole4 == False:
        pallet.hole4 = True
        pallet.hole4Content = product.name
    elif pallet.hole5 == False:
        pallet.hole5 = True
        pallet.hole5Content = product.name
    elif pallet.hole6 == False:
        pallet.hole6 = True
        pallet.hole6Content = product.name
    elif pallet.hole7 == False:
        pallet.hole7 = True
        pallet.hole7Content = product.name
    elif pallet.hole8 == False:
        pallet.hole8 = True
        pallet.hole8Content = product.name
    elif pallet.hole9 == False:
        pallet.hole9 = True
        pallet.hole9Content = product.name
    else:
        pass
    pallet.save()
    rate = np.array([pallet.hole1, pallet.hole2, pallet.hole3, pallet.hole4,
                     pallet.hole5, pallet.hole6, pallet.hole7, pallet.hole8, pallet.hole9])
    pallet.rate = round(np.sum(rate)/9, 2)
    pallet.save()
    storePosition = pallet.position
    storePosition.status = '3'
    storePosition.save()
    product.pallet = pallet
    product.save()
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
    return JsonResponse({'res': '18,'})


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
            map(lambda obj: obj.name, OrderType.objects.all()))}
    if params['model'] == 'store':
        selectList = {'storeType': list(
            map(lambda obj: obj.name, StoreType.objects.all())), 'workShop': list(
            map(lambda obj: obj.name, WorkShop.objects.all()))}
    if params['model'] == 'device':
        selectList = {'deviceType': list(
            map(lambda obj: obj.name, DeviceType.objects.all())), 'process': list(
            map(lambda obj: obj.name, Process.objects.all()))}
    if params['model'] == 'user':
        roles = Role.objects.all()
        departments = Department.objects.all()
        selectList = {'gender': ['男', '女'],
                      'role': list(map(lambda obj: obj.name, roles)), 'department': list(map(lambda obj: obj.name, departments))}
    return JsonResponse({'res': selectList})


@csrf_exempt
def updateProcessByRoute(request):

    def updateDevice(obj):
        obj.process = None
        obj.save()
    params = json.loads(request.body)
    list(map(lambda obj: updateDevice(obj), Device.objects.filter(
        Q(process__route__key=params['key']))))
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
                product = Product()
                product.name = workOrder.description.split(',')[
                    0].split(':')[1]
                product.number = str(time.time()*1000000)
                product.workOrder = workOrder
                product.save()
    return JsonResponse({'res': 'ok'})


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
def updateCount(request):
    params = json.loads(request.body)
    doc = Document.objects.get(key=params['key'])
    doc.count = params['count']+1
    doc.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def updateDevice(request):
    params = json.loads(request.body)
    device = Device.objects.get(key=params['key'])
    if params['process'] != '':
        process = Process.objects.get(
            Q(name=params['process'], route__key=params['route']))
        device.process = process
    else:
        device.process = None
    device.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def upload(request):
    up = request.POST['up']
    f = request.FILES['file']
    with open(BASE_DIR+'/static/document/'+f.name, 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    document = Document()
    document.up = up
    document.name = f.name
    document.path = 'http://127.0.0.1:8899/static/document/%s' % f.name
    document.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def uploadPic(request):
    route = request.POST['route']
    process = request.POST['process']
    pro = Process.objects.get(Q(name=process, route__key=route))
    f = request.FILES['file']
    with open(BASE_DIR+'/static/picture/'+f.name, 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    pro.path = 'http://127.0.0.1:8899/static/picture/%s' % f.name
    pro.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def createStore(request):
    params = json.loads(request.body)
    count = params['row']*params['column']
    for i in range(count):
        position = StroePosition()
        position.store = Store.objects.get(key=params['key'])
        position.number = '%s' % str(i+1)
        position.status = '1'
        position.save()
        pallet = Pallet()
        pallet.position = StroePosition.objects.get(
            number='%s' % str(i+1))
        pallet.number = str(i+1)
        pallet.save()
    return JsonResponse({'res': 'ok'})
