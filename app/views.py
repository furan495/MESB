import os
import re
import json
import time
import random
import pypinyin
import datetime
import numpy as np
import pandas as pd
from app.utils import *
from app.models import *
from app.serializers import *
from itertools import product
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models.aggregates import Count, Sum, Max, Min, Avg

# Create your views here.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@csrf_exempt
def recordWeight(request):
    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')
    print(params)
    try:
        workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], description__icontains=color[params[2]], order=Order.objects.get(number=params[3])))
        product = Product.objects.get(workOrder=workOrder)
        standard = ProductStandard.objects.get(
            Q(name='重量', product=product))
        standard.realValue = float(params[4])
        if np.abs(standard.realValue-float(standard.expectValue)) <= product.prodType.errorRange:
            standard.result = '1'
            product.result = '1'
        else:
            standard.result = '2'
            product.result = '2'
            product.reason = '重量不足'
        standard.save()
        product.save()
    except:
        pass

    return JsonResponse({'res': 'ok'})


@csrf_exempt
def wincc(request):

    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    position = {'LP': '理瓶', 'XG': '旋盖', 'SLA': '数粒A',
                'SLB': '数粒B', 'SLC': '数粒C', 'CZ': '称重', 'TB': '贴签', 'HJ': '桁架'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')

    print(params)

    if position[params[0]] == '理瓶':
        bottle = Bottle.objects.filter(
            Q(order__number=params[3], number='', color=color[params[2]]))[0]
        bottle.number = params[1]
        bottle.save()
        workOrder = WorkOrder.objects.filter(
            Q(description__icontains=color[params[2]], bottle=None, status__name='等待中', order=Order.objects.get(number=params[3]))).order_by('createTime')[0]
        workOrder.bottle = params[1]
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        workOrder.save()
        order = workOrder.order
        order.status = OrderStatus.objects.get(Q(name='加工中'))
        order.save()
        Material.objects.filter(Q(name=color[params[2]]))[0].delete()

    try:
        if position[params[0]] == '数粒A':
            workOrder = WorkOrder.objects.get(
                Q(bottle=params[1], status__name='加工中'))
            red = workOrder.description.split(',')[1].split(':')[1]
            for i in range(int(red)):
                Material.objects.filter(Q(name='红粒'))[0].delete()
        if position[params[0]] == '数粒B':
            workOrder = WorkOrder.objects.get(
                Q(bottle=params[1], status__name='加工中'))
            green = workOrder.description.split(',')[1].split(':')[1]
            for i in range(int(green)):
                Material.objects.filter(Q(name='绿粒'))[0].delete()
        if position[params[0]] == '数粒C':
            workOrder = WorkOrder.objects.get(
                Q(bottle=params[1], status__name='加工中'))
            blue = workOrder.description.split(',')[1].split(':')[1]
            for i in range(int(blue)):
                Material.objects.filter(Q(name='蓝粒'))[0].delete()
        if position[params[0]] == '旋盖':
            Material.objects.filter(Q(name='瓶盖'))[0].delete()
        event = Event()
        event.workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], description__icontains=color[params[2]], order=Order.objects.get(number=params[3])))
        event.bottle = params[1]
        event.source = position[params[0]]
        event.title = '进入%s单元' % position[params[0]]
        event.save()
    except Exception as e:
        print(e, '这里有问题')

    eventList = list(map(lambda obj: obj.source,
                         Event.objects.filter(Q(bottle=params[1], workOrder__order__number=params[3], workOrder__status__name='加工中'))))
    try:
        route = Order.objects.get(number=params[3]).route
        processList = list(
            map(lambda obj: obj['text'], json.loads(route.data)['nodeDataArray']))
        if len(eventList) == 0 or processList[:len(eventList)] != eventList:
            workOrder = WorkOrder.objects.get(
                Q(bottle=params[1], order=Order.objects.get(number=params[3])))
            workOrder.status = WorkOrderStatus.objects.get(name='失败')
            workOrder.endTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            workOrder.save()
            with open(BASE_DIR+'/listen.txt', 'w') as f:
                f.write('工单号:%s-瓶号:%s' % (workOrder.number, workOrder.bottle))
    except Exception as e:
        print(e, '这里有问题222')
    return JsonResponse({'res': 'res'})


@csrf_exempt
def storeOperate(request):

    def updatePalletContent(hole, params, holeContent):
        if hole:
            return params if holeContent == None or holeContent == '' else holeContent
        else:
            return params if params != '0' else ''

    def updatePalletHole(hole, holeContent):
        if hole:
            return True
        else:
            return True if holeContent != '0' else False

    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')
    print(params)
    store = Store.objects.get(Q(storeType__name='成品库'))
    storePosition = StorePosition.objects.get(
        Q(number='%s-%s' % (params[-1], store.key)))
    storePosition.status = '3'
    storePosition.save()
    pallet = Pallet.objects.get(
        Q(number=params[-2], position__store__storeType__name='成品库'))
    pallet.position = storePosition
    pallet.hole1 = updatePalletHole(pallet.hole1, params[2])
    pallet.hole2 = updatePalletHole(pallet.hole2, params[3])
    pallet.hole3 = updatePalletHole(pallet.hole3, params[4])
    pallet.hole4 = updatePalletHole(pallet.hole4, params[5])
    pallet.hole5 = updatePalletHole(pallet.hole5, params[6])
    pallet.hole6 = updatePalletHole(pallet.hole6, params[7])
    pallet.hole7 = updatePalletHole(pallet.hole7, params[8])
    pallet.hole8 = updatePalletHole(pallet.hole8, params[9])
    pallet.hole9 = updatePalletHole(pallet.hole9, params[10])
    pallet.save()
    rate = np.array([pallet.hole1, pallet.hole2, pallet.hole3, pallet.hole4,
                     pallet.hole5, pallet.hole6, pallet.hole7, pallet.hole8, pallet.hole9])
    pallet.rate = round(np.sum(rate)/9, 2)
    pallet.hole1Content = updatePalletContent(
        pallet.hole1, params[2], pallet.hole1Content)
    pallet.hole2Content = updatePalletContent(
        pallet.hole2, params[3], pallet.hole2Content)
    pallet.hole3Content = updatePalletContent(
        pallet.hole3, params[4], pallet.hole3Content)
    pallet.hole4Content = updatePalletContent(
        pallet.hole4, params[5], pallet.hole4Content)
    pallet.hole5Content = updatePalletContent(
        pallet.hole5, params[6], pallet.hole5Content)
    pallet.hole6Content = updatePalletContent(
        pallet.hole6, params[7], pallet.hole6Content)
    pallet.hole7Content = updatePalletContent(
        pallet.hole7, params[8], pallet.hole7Content)
    pallet.hole8Content = updatePalletContent(
        pallet.hole8, params[9], pallet.hole8Content)
    pallet.hole9Content = updatePalletContent(
        pallet.hole9, params[10], pallet.hole9Content)
    pallet.save()

    for bottle in params[2:-2]:
        if bottle != '0':
            try:
                workOrder = WorkOrder.objects.get(
                    Q(bottle=bottle, status__name='加工中'))
                workOrder.status = WorkOrderStatus.objects.get(name='已完成')
                workOrder.endTime = datetime.datetime.now()
                workOrder.save()
                bot = Bottle.objects.get(
                    Q(number=bottle, order__number=params[1]))
                bot.status = BottleState.objects.get(Q(name='入库'))
                bot.save()
                product = workOrder.workOrder
                product.pallet = pallet
                product.save()
                event = Event()
                event.workOrder = workOrder
                event.bottle = bottle
                event.source = '立库'
                event.title = '进入立库单元'
                event.save()
            except Exception as e:
                try:
                    workOrder = WorkOrder.objects.filter(
                        Q(bottle=bottle, status__name='失败'))[0]
                    workOrder.save()
                    bottle = Bottle.objects.get(
                        Q(number=bottle, order__number=params[1]))
                    bottle.status = BottleState.objects.get(Q(name='入库'))
                    bottle.save()
                    product = workOrder.workOrder
                    product.pallet = pallet
                    product.save()
                    event = Event()
                    event.workOrder = workOrder
                    event.bottle = bottle
                    event.source = '立库'
                    event.title = '进入立库单元'
                    event.save()
                except Exception as e:
                    print(e)

    if len(WorkOrder.objects.filter(Q(status__name='等待中', order__number=params[1]))) == 0:
        order = Order.objects.get(number=params[1])
        order.status = OrderStatus.objects.get(name='已完成')
        order.save()
    return JsonResponse({'res': 'res'})


@csrf_exempt
def queryPallet(request):
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))
    bottles = Bottle.objects.filter(
        Q(order=Order.objects.get(number=params['number'])))
    num = -int(len(bottles)/9) if len(bottles)/9 > 1 else -1
    pallets = ','.join(list(map(lambda obj: obj.position.number, list(
        Pallet.objects.filter(Q(rate__lt=0.67)))[:num])))
    print('%s,' % pallets.split('-')[0])
    return JsonResponse({'res': '8,'})


@csrf_exempt
def OutputPallet(request):
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))
    pallet = Pallet.objects.get(
        Q(number=params['pallet'], position__store__storeType__name='成品库'))
    position = pallet.position
    position.status = '2'
    position.save()
    pallet.position = None
    pallet.save()
    print(params)
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def loginCheck(request):
    params = json.loads(request.body)
    user = User.objects.get(phone=params['phone'])
    res = ''
    if user.password == params['password']:
        res = {'name': user.name, 'authority': user.role.authority, 'key': user.key, 'state': user.state,
               'role': user.role.name, 'phone': user.phone}
    else:
        res = 'err'
    return JsonResponse({'res': res})


@csrf_exempt
def updateUserState(request):
    params = json.loads(request.body)
    user = User.objects.get(key=params['key'])
    user.state = params['state']
    user.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def logoutUser(request):
    params = json.loads(request.body)
    user = User.objects.get(
        Q(phone=params['phone'], password=params['password']))
    user.state = '1'
    user.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def logout(request):
    params = json.loads(request.body)
    print(params)
    """ user = User.objects.get(
        Q(phone=params['phone'], password=params['password']))
    user.state = '1'
    user.save() """
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def checkUserState(request):
    params = json.loads(request.body)
    user = User.objects.get(key=params['key'])
    return JsonResponse({'res': user.state})


@csrf_exempt
def querySelect(request):
    """ for i in range(20):
        user=User()
        user.name='用户%s' % str(i+1)
        user.password='123456'
        user.role=Role.objects.get(Q(name='管理员'))
        user.gender='1'
        user.post='软件工程师'
        user.department=Organization.objects.get(Q(name='研发部'))
        user.phone='user-%s' % str(i+1)
        user.save() """
    """ data = Order.objects.filter(Q(status__name='已完成')).values('customer', 'number').annotate(
        workOrders=Count('workOrders'),startTime=Min('workOrders__startTime'),endTime=Max('workOrders__endTime'),times=Max('workOrders__endTime')-Min('workOrders__startTime'),rate=Count('workOrders__workOrder')/Count('workOrders__workOrder')).values('customer__name', 'customer__level', 'customer__number','number','batch','createTime','scheduling','workOrders','status__name','startTime','endTime','times','rate')

    print(data.query.__str__()) """

    """ for i in range(500):
        material = Material()
        material.name = '蓝粒'
        material.unit = '个'
        material.size = 'blue'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save() """
    """ for i in range(500):
        material = Material()
        material.name = '红粒'
        material.unit = '个'
        material.size = 'red'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save()
    for i in range(500):
        material = Material()
        material.name = '红瓶'
        material.unit = '个'
        material.size = 'rbottle'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save()
    for i in range(500):
        material = Material()
        material.name = '绿瓶'
        material.unit = '个'
        material.size = 'gbottle'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save()
    for i in range(500):
        material = Material()
        material.name = '蓝瓶'
        material.unit = '个'
        material.size = 'bbottle'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save()
    for i in range(500):
        material = Material()
        material.name = '绿粒'
        material.unit = '个'
        material.size = 'green'
        material.mateType = '2'
        material.store = Store.objects.get(name='原料库')
        material.save() """

    """ data = Order.objects.filter(Q(status__name='等待中')).values('number', 'scheduling', 'status__name').annotate(rbot=Count('bottles', filter=Q(bottles__color='红瓶')), gbot=Count('bottles', filter=Q(bottles__color='绿瓶')), bbot=Count('bottles', filter=Q(bottles__color='蓝瓶')), rred=Sum('bottles__red', filter=Q(bottles__color='红瓶')) if Sum('bottles__red', filter=Q(bottles__color='红瓶'))==1 else Avg('bottles__red', filter=Q(bottles__color='红瓶')), gred=Sum('bottles__red', filter=Q(bottles__color='绿瓶')), bred=Sum('bottles__red', filter=Q(bottles__color='蓝瓶')), rgreen=Sum('bottles__green', filter=Q(bottles__color='红瓶')), ggreen=Sum('bottles__green', filter=Q(bottles__color='绿瓶')), bgreen=Sum('bottles__green', filter=Q(bottles__color='蓝瓶')), rblue=Sum('bottles__blue', filter=Q(bottles__color='红瓶')), gblue=Sum('bottles__blue', filter=Q(bottles__color='绿瓶')), bblue=Sum('bottles__blue', filter=Q(bottles__color='蓝瓶'))).values('number', 'scheduling', 'status__name', 'rbot', 'gbot', 'bbot', 'rred', 'gred', 'bred', 'rgreen', 'ggreen', 'bgreen', 'rblue', 'gblue', 'bblue')

    print(data.query.__str__()) """

    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order' or params['model'] == 'productType':
        selectList = {
            'route': list(map(lambda obj: obj.name, ProcessRoute.objects.all())),
            'customer': list(map(lambda obj: obj.name, Customer.objects.all())),
            'orderType': list(map(lambda obj: obj.name, OrderType.objects.all())),
            'product': list(map(lambda obj: [obj.name, obj.orderType.name], ProductType.objects.all()))
        }
    if params['model'] == 'bom':
        selectList = {
            'materials': list(set(list(map(lambda obj: obj.name, Material.objects.all())))),
            'product': list(map(lambda obj: obj.name, ProductType.objects.filter(Q(bom=None)))),
        }
    if params['model'] == 'store':
        selectList = {
            'workShop': list(map(lambda obj: obj.name, WorkShop.objects.all())),
            'storeType': list(map(lambda obj: obj.name, StoreType.objects.all())),
        }
    if params['model'] == 'productLine':
        selectList = {
            'state': list(map(lambda obj: obj.name, LineState.objects.all())),
            'workShop': list(map(lambda obj: obj.name, WorkShop.objects.all()))
        }
    if params['model'] == 'device':
        selectList = {
            'process': list(map(lambda obj: obj.name, Process.objects.all())),
            'deviceType': list(map(lambda obj: obj.name, DeviceType.objects.all())),
        }
    if params['model'] == 'document':
        selectList = {
            'docType': list(map(lambda obj: [obj.name, obj.key], DocType.objects.all()))
        }
    if params['model'] == 'productStandard':
        selectList = {
            'result': ['合格', '不合格'],
            'product': list(map(lambda obj: obj.name, Product.objects.filter(Q(result=1)))),
        }
    if params['model'] == 'material':
        selectList = {
            'mateType': ['自制', '外采'],
            'store__name': list(map(lambda obj: obj.name, Store.objects.all())),
        }
    if params['model'] == 'tool':
        selectList = {
            'toolType': ['自制', '外采'],
            'store__name': list(map(lambda obj: obj.name, Store.objects.all())),
        }
    if params['model'] == 'organization':
        selectList = {
            'level': list(map(lambda obj: obj.name, OrgaLevel.objects.all())),
            'parent': list(map(lambda obj: obj['parent'], Organization.objects.all().values('parent').distinct())),
        }
    if params['model'] == 'user':
        selectList = {
            'gender': ['男', '女'],
            'role': list(map(lambda obj: obj.name,  Role.objects.all())),
            'department': list(map(lambda obj: obj.name, Organization.objects.filter(Q(level__name='部门'))))
        }
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
    order.status = OrderStatus.objects.get(name='已排产')
    order.batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order.scheduling = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order.save()
    for description in orderDesc:
        if len(description.split(',')) > 1:
            for i in range(int(description.split(',')[-1].split(':')[1])):
                workOrder = WorkOrder()
                workOrder.order = order
                time.sleep(0.1)
                workOrder.number = str(time.time()*1000000)[:15]
                workOrder.status = WorkOrderStatus.objects.get(name='等待中')
                workOrder.description = ','.join(description.split(',')[:4])
                workOrder.save()

                product = Product()
                product.name = '%s/%s' % (workOrder.description.split(',')[
                    0].split(':')[1], workOrder.number)
                product.number = str(time.time()*1000000)
                product.workOrder = workOrder
                product.prodType = ProductType.objects.get(Q(orderType=order.orderType, name__icontains=workOrder.description.split(',')[
                    0].split(':')[1]))
                product.save()

                standard = ProductStandard()
                standard.name = '重量'
                standard.expectValue = str(np.sum(list(map(lambda obj: int(obj)*5, re.findall(
                    '\d+', description[:description.index('份数')])))))
                standard.product = product
                standard.save()
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
    url = request.POST['url']
    f = request.FILES['file']
    with open(BASE_DIR+'/upload/document/'+''.join(list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'), 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    document = Document()
    document.up = up
    document.name = f.name
    document.path = 'http://%s:8899/upload/document/%s' % (url, ''.join(
        list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'))
    document.save()
    operate = Operate()
    operate.name = '上传文档'
    operate.target = f.name
    operate.operator = up
    operate.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def uploadPic(request):
    url = request.POST['url']
    route = request.POST['route']
    process = request.POST['process']
    pro = Process.objects.get(Q(name=process, route__key=route))
    f = request.FILES['file']
    with open(BASE_DIR+'/upload/picture/'+''.join(list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'), 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    pro.path = 'http://%s:8899/upload/picture/%s' % (url, ''.join(
        list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'))
    pro.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def updatePWD(request):
    params = json.loads(request.body)
    user = User.objects.get(phone=params['phone'])
    user.password = params['pwd']
    user.save()
    return JsonResponse({'res': 'succ'})


@csrf_exempt
def createStore(request):
    params = json.loads(request.body)
    count = params['row']*params['column']
    for i in range(count):
        position = StorePosition()
        position.store = Store.objects.get(key=params['key'])
        position.number = '%s-%s' % (str(i+1), params['key'])
        position.status = '1'
        position.save()
        pallet = Pallet()
        pallet.position = StorePosition.objects.get(
            number='%s-%s' % (str(i+1), params['key']))
        pallet.number = str(i+1)
        pallet.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def queryOperateChart(request):

    dikaer = []
    for x, y in product(range(10), range(10)):
        dikaer.append([x, y])

    def valueSelect(name):
        if '新增' in name:
            return 1
        if '删除' in name:
            return 3
        if '预览' in name:
            return 5
        if '上传' in name:
            return 7
        if '排产' in name:
            return 9
        if '登陆' in name:
            return 11

    series = []
    data = [{'data': series}]
    operateList = Operate.objects.all().order_by('-time')
    for i in range(len(operateList) if len(operateList) <= 100 else 100):
        ope = {}
        ope['x'] = dikaer[i][0]
        ope['y'] = dikaer[i][1]
        ope['operate'] = operateList[i].name
        ope['operator'] = operateList[i].operator
        ope['value'] = valueSelect(operateList[i].name)
        ope['time'] = operateList[i].time.strftime('%Y-%m-%d %H:%M:%S')
        series.append(ope)

    return JsonResponse({'res': data})


@csrf_exempt
def queryQualanaChart(request):
    data = qualAna()
    return JsonResponse({'res': data})


@csrf_exempt
def annotateDataList(request):
    def addkey(obj, objs):
        obj['key'] = objs.index(obj)
        return obj
    params = json.loads(request.body)
    if params['model'] == 'material':
        queryset = Material.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'mateType', 'store__name')
    else:
        queryset = Tool.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'toolType', 'store__name')
    return JsonResponse({'res': list(map(lambda obj: addkey(obj, list(queryset)), list(queryset)))})


@csrf_exempt
def exportData(request):
    res = ''
    params = json.loads(request.body)
    if params['model'] == 'workShop':
        excel = list(
            map(lambda obj: {
                '车间编号': obj.number, '车间名称': obj.name, '车间描述': obj.descriptions},
                WorkShop.objects.all())
        )
    if params['model'] == 'productLine':
        excel = list(
            map(lambda obj: {
                '产线名称': obj.name, '隶属车间': obj.workShop.name, '产线编号': obj.number, '产线状态': obj.state.name, '产线描述': obj.description}, ProductLine.objects.all())
        )
    if params['model'] == 'processRoute':
        excel = list(
            map(lambda obj: {
                '工艺名称': obj.name, '工艺描述': obj.description, '创建人': obj.creator, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'),
                '包含工序': ('->').join(list(
                    map(lambda obj: obj.name,
                        Process.objects.filter(Q(route=obj))
                        ))
                ), '详细数据': obj.data},
                ProcessRoute.objects.all())
        )
    if params['model'] == 'store':
        excel = list(
            map(lambda obj: {
                '仓库名称': obj.name, '隶属车间': obj.workShop.name, '仓库编号': obj.number, '仓库类型': obj.storeType.name, '仓库规模': obj.dimensions},
                Store.objects.all())
        )
    if params['model'] == 'device':
        excel = list(
            map(lambda obj: {
                '设备名称': obj.name, '设备类型': obj.deviceType.name, '设备状态': list(DeviceState.objects.filter(Q(device=obj)))[-1].name,
                '所在工序': obj.process.name if obj.process else '', '设备编号': obj.number, '入库时间': obj.joinTime.strftime('%Y-%m-%d %H:%M:%S'),
                '设备厂家': obj.factory, '出厂日期': obj.facTime, '厂家联系人': obj.facPeo, '厂家电话': obj.facPho},
                Device.objects.all())
        )
    if params['model'] == 'material':
        excel = list(
            map(lambda obj: {
                '物料名称': obj['name'], '物料规格': obj['size'], '基本单位': obj['unit'], '物料类型': '自制' if obj['mateType'] == '1' else '外采',
                '现有库存': obj['counts'], '存储仓库': Store.objects.get(key=obj['store']).name},
                Material.objects.all().values('name')
                .annotate(counts=Count('size'))
                .values('name', 'size', 'counts', 'unit', 'mateType', 'store'))
        )
    if params['model'] == 'tool':
        excel = list(
            map(lambda obj: {
                '工具名称': obj['name'], '工具规格': obj['size'], '基本单位': obj['unit'], '工具类型': '自制' if obj['toolType'] == '1' else '外采',
                '现有库存': obj['counts'], '存储仓库': Store.objects.get(key=obj['store']).name},
                Tool.objects.all().values('name')
                .annotate(counts=Count('size'))
                .values('name', 'size', 'counts', 'unit', 'toolType', 'store'))
        )
    if params['model'] == 'bom':
        excel = list(
            map(lambda obj: {
                '对应产品': obj.product.name, 'bom名称': obj.name, '创建人': obj.creator, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'),
                'bom内容': obj.content},
                BOM.objects.all())
        )
    if params['model'] == 'productType':
        excel = list(
            map(lambda obj: {
                '产品名称': obj.name, '订单类型': obj.orderType.name, '产品编号': obj.number, '产品容差': obj.errorRange},
                ProductType.objects.all())
        )
    if params['model'] == 'product':
        excel = list(
            map(lambda obj: {
                '成品名称': obj.name, '成品编号': obj.number, '对应工单': obj.workOrder.number, '成品批次': obj.batch.strftime('%Y-%m-%d'),
                '质检结果': '合格' if obj.result == '1' else '不合格', '存放仓位': selectPosition(obj),
                '历史状态': ('->').join(list(
                    map(lambda event: '%s/%s' % (event.time.strftime('%Y-%m-%d %H:%M:%S'), event.title),
                        Event.objects.filter(Q(workOrder=obj.workOrder))
                        ))
                )}, Product.objects.all())
        )
    if params['model'] == 'order':
        excel = list(
            map(lambda obj: {
                '订单类别': obj.orderType.name, '选用工艺': obj.route.name, '订单状态': obj.status.name, '创建人': obj.creator, '目标客户': obj.customer.name, '订单编号': obj.number,
                '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), '排产时间': obj.scheduling, '订单批次': obj.batch, '订单描述': obj.description},
                Order.objects.all())
        )
    if params['model'] == 'workOrder':
        excel = list(
            map(lambda obj: {
                '工单状态': obj.status.name, '工单编号': obj.number, '订单编号': obj.order.number, '工单瓶号': obj.bottle,
                '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), '开始时间': obj.startTime, '结束时间': obj.endTime, '工单描述': obj.description},
                WorkOrder.objects.all())
        )
    if params['model'] == 'unqualified':
        excel = list(
            map(lambda obj: {
                '成品名称': obj.name, '成品编号': obj.number, '对应工单': obj.workOrder.number, '成品批次': obj.batch.strftime('%Y-%m-%d'),
                '不合格原因': obj.reason, '存放仓位': selectPosition(obj)},
                Product.objects.filter(result='2'))
        )
    if params['model'] == 'productStandard':
        excel = list(
            map(lambda obj: {
                '产品名称': obj.product.name, '标准名称': obj.name, '预期结果': obj.expectValue, '实际结果': obj.realValue,
                '检测结果': '合格' if obj.result == '1' else '不合格'},
                ProductStandard.objects.all())
        )
    if params['model'] == 'role':
        excel = list(
            map(lambda obj: {'角色名': obj.name, '权限范围': obj.authority},
                Role.objects.all())
        )
    if params['model'] == 'user':
        excel = list(
            map(lambda obj: {'角色': obj.role.name, '姓名': obj.name, '性别': '男' if obj.gender == '1' else '女', '部门': obj.department.name if obj.department else '', '职位': obj.post, '电话': obj.phone},
                User.objects.all())
        )
    if params['model'] == 'mateAna':
        data = Bottle.objects.all().values('createTime').annotate(
            cup=Count('color'), rbot=Count('color', filter=Q(color='红瓶')), gbot=Count('color', filter=Q(color='绿瓶')), bbot=Count('color', filter=Q(color='蓝瓶')), reds=Sum('red'), greens=Sum('green'), blues=Sum('blue')).values('createTime', 'cup', 'rbot', 'gbot', 'bbot', 'reds', 'greens', 'blues')
        excel = list(
            map(lambda obj: {'日期': obj['createTime'].strftime('%Y-%m-%d'), '瓶盖': obj['cup'], '红瓶': obj['rbot'],
                             '绿瓶': obj['gbot'], '蓝瓶': obj['bbot'], '红粒': obj['reds'], '绿粒': obj['greens'], '蓝粒': obj['blues']}, data)
        )
    if params['model'] == 'powerAna':
        data = Bottle.objects.all().values('order').annotate(
            expects=Count('order'), reals=Count('order', filter=Q(status__name='入库'))).values('order__number', 'expects', 'reals')
        rate = list(map(lambda obj: round(len(Product.objects.filter(
            Q(result='1', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))) if len(WorkOrder.objects.filter(Q(order=obj))) != 0 else 1, 2), Order.objects.all()))
        excel = list(
            map(lambda obj: {'订单号': obj[0]['order__number'], '预期产量': obj[0]['expects'], '实际产量': obj[0]['reals'],
                             '合格率': obj[1]}, list(zip(data, rate)))
        )
    if params['model'] == 'qualAna':
        data = Product.objects.all().values('batch').annotate(good=Count('result', filter=Q(
            result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
        excel = list(
            map(lambda obj: {'日期': obj['batch'].strftime('%Y-%m-%d'), '合格数': obj['good'], '不合格数': obj['bad'],
                             '合格率': round(obj['good']/(obj['good']+obj['bad']), 2), '不合格率': round(obj['bad']/(obj['good']+obj['bad']), 2)}, data)
        )
    if params['model'] == 'customer':
        excel = list(
            map(lambda obj: {'客户名称': obj.name, '客户编号': obj.number, '联系电话': obj.phone,
                             '客户等级': obj.level, '公司': obj.company}, Customer.objects.all())
        )

    df = pd.DataFrame(excel)
    df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
    return JsonResponse({'res': 'http://%s:8899/upload/export/export.xlsx' % params['url']})


@csrf_exempt
def queryPoweranaChart(request):
    data = powerAna()
    return JsonResponse({'res': data, 'xaxis': list(map(lambda obj: obj.number, Order.objects.all()))})


@csrf_exempt
def queryMateanaChart(request):
    data = mateAna()
    return JsonResponse({'res': data})


@csrf_exempt
def filterChart(request):
    data = []
    params = json.loads(request.body)
    if params['chart'] == 'power':
        data = [
            {'name': '预期产量', 'type': 'column', 'data': list(map(lambda obj:  len(
                WorkOrder.objects.filter(Q(order=obj))), Order.objects.filter(Q(createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d')))))},
            {'name': '实际产量', 'type': 'column', 'data':  list(map(lambda obj:   len(
                WorkOrder.objects.filter(Q(status__name='已完成', order=obj))), Order.objects.filter(Q(createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d')))))},
            {'name': '合格率', 'type': 'column', 'data': list(map(lambda obj: round(len(Product.objects.filter(
                Q(result='1', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))) if len(WorkOrder.objects.filter(Q(order=obj))) != 0 else 1, 2), Order.objects.filter(Q(createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d')))))},
        ]
    if params['chart'] == 'qual':
        product = Product.objects.filter(Q(workOrder__order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), workOrder__order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('batch').annotate(good=Count('result', filter=Q(
            result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
        goodData = list(
            map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                             * 1000+8*60*60*1000, obj['good']], product))
        badData = list(
            map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                             * 1000+8*60*60*1000, obj['bad']], product))
        goodRate = list(
            map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                             * 1000+8*60*60*1000, round(obj['good']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) != 0 else 1, 2)], product))
        reasonData = list(
            map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
                Product.objects.filter(Q(result='2'))
                .values('reason')
                .annotate(count=Count('reason'))
                .values('reason', 'count'))
        )
        data = [
            {'name': '合格', 'type': 'column', 'yAxis': 0, 'data': goodData},
            {'name': '合格率', 'type': 'spline', 'yAxis': 1, 'data': goodRate},
            {'name': '不合格', 'type': 'column', 'yAxis': 0, 'data': badData},
            {'name': '总计', 'type': 'pie', 'color': '#00C1FF', 'data': reasonData,
                'center': [150, 50], 'size':150}
        ]
    if params['chart'] == 'mate':
        redBottle = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
                Bottle.objects.filter(Q(color='红瓶', order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        greenBottle = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
                Bottle.objects.filter(Q(color='绿瓶', order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        blueBottle = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
                Bottle.objects.filter(Q(color='蓝瓶', order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        cap = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
                Bottle.objects.filter(Q(order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        red = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['reds'], 1],
                Bottle.objects.filter(Q(order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime', 'order', 'red').annotate(
                    reds=Sum('red')).values('createTime', 'reds').annotate(count=Count('red')).values('createTime', 'reds')
                ))
        green = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['greens'], 1],
                Bottle.objects.filter(Q(order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime', 'order', 'green').annotate(
                    greens=Sum('green')).values('createTime', 'greens').annotate(count=Count('green')).values('createTime', 'greens')
                ))
        blue = list(
            map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['blues'], 1],
                Bottle.objects.filter(Q(order__createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), order__createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d'))).values('createTime', 'order', 'blue').annotate(
                    blues=Sum('blue')).values('createTime', 'blues').annotate(count=Count('blue')).values('createTime', 'blues')
                ))
        data = [
            {'name': '瓶盖', 'type': 'spline', 'data': cap},
            {'name': '红瓶', 'type': 'column','data': redBottle},
            {'name': '绿瓶', 'type': 'column',  'data': greenBottle},
            {'name': '蓝瓶', 'type': 'column', 'data': blueBottle},
            {'name': '红粒', 'type': 'spline', 'yAxis': 1,'data': red},
            {'name': '绿粒', 'type': 'spline', 'yAxis': 1,'data': green},
            {'name': '蓝粒', 'type': 'spline', 'yAxis': 1,'data': blue},
        ]
    return JsonResponse({'res': data, 'xaxis': list(map(lambda obj: obj.number, Order.objects.filter(Q(createTime__gte=datetime.datetime.strptime(params['start'], '%Y/%m/%d'), createTime__lte=datetime.datetime.strptime(params['stop'], '%Y/%m/%d')))))})


@csrf_exempt
def splitCheck(request):
    params = json.loads(request.body)
    descriptions = params['description'].split(';')[:-1]
    res, material = 'ok', ''
    rbot, gbot, bbot, cap, red, green, blue = 0, 0, 0, 0, 0, 0, 0
    for desc in descriptions:
        count = desc.split(',')[-1].split(':')[1]
        red = red+int(desc.split(',')[1].split(':')[1])*int(count)
        green = green+int(desc.split(',')[2].split(':')[1])*int(count)
        blue = blue+int(desc.split(',')[3].split(':')[1])*int(count)
        if desc.split(',')[0].split(':')[1] == '红瓶':
            rbot = rbot+int(count)
        if desc.split(',')[0].split(':')[1] == '绿瓶':
            gbot = gbot+int(count)
        if desc.split(',')[0].split(':')[1] == '蓝瓶':
            bbot = bbot+int(count)
    if red > Material.objects.filter(Q(name='红粒')).count():
        res = 'err'
        material = '红粒不足，无法排产'
    if green > Material.objects.filter(Q(name='绿粒')).count():
        res = 'err'
        material = '绿粒不足，无法排产'
    if blue > Material.objects.filter(Q(name='蓝粒')).count():
        res = 'err'
        material = '蓝粒不足，无法排产'
    if (rbot+gbot+bbot) > Material.objects.filter(Q(name='瓶盖')).count():
        res = 'err'
        material = '瓶盖不足，无法排产'
    if rbot > Material.objects.filter(Q(name='红瓶')).count():
        res = 'err'
        material = '红瓶不足，无法排产'
    if gbot > Material.objects.filter(Q(name='绿瓶')).count():
        res = 'err'
        material = '绿瓶不足，无法排产'
    if bbot > Material.objects.filter(Q(name='蓝瓶')).count():
        res = 'err'
        material = '蓝瓶不足，无法排产'

    return JsonResponse({'res': res, 'material': material})


@csrf_exempt
def queryOrganization(request):
    data = list(
        map(lambda company: {'title': company.name, 'key': company.key, 'children': list(
            map(lambda department: {'title': department.name, 'key': department.key, 'children': list(
                map(lambda member: {'title': member.name, 'key': member.key}, User.objects.filter(
                    Q(department__name=department.name)))
            )}, Organization.objects.filter(
                Q(level__name='部门', parent=company.name)))
        )}, Organization.objects.filter(Q(level__name='公司')))
    )

    series = list(map(lambda obj: [obj.parent, obj.name],
                      Organization.objects.filter(Q(level__name='部门'))))
    seriesId = list(map(lambda obj: [obj.name, obj.key],
                        Organization.objects.filter(Q(level__name='部门'))))

    nodes = list(map(lambda obj: {'id': obj.name, 'name': obj.name,
                                  'title': User.objects.filter(Q(department__name=obj.name, post='部长'))[0].name if len(User.objects.filter(Q(department__name=obj.name, post='部长'))) == 1 else ''}, Organization.objects.filter(Q(level__name='部门'))))
    nodesId = list(map(lambda obj: {'id': obj.key, 'name': obj.duty},
                       Organization.objects.filter(Q(level__name='部门'))))
    list(map(lambda obj: series.append(obj), seriesId))
    list(map(lambda obj: nodes.append(obj), nodesId))

    return JsonResponse({'tree': data, 'series': series, 'nodes': nodes})


errTime = 0
@csrf_exempt
def queryProducing(request):
    global errTime
    info = ''
    if os.path.exists(BASE_DIR+'/listen.txt'):
        errTime = errTime+1
        with open(BASE_DIR+'/listen.txt') as f:
            info = f.read()

    if errTime == 3:
        errTime = 0
        if os.path.exists(BASE_DIR+'/listen.txt'):
            os.remove(BASE_DIR+'/listen.txt')

    workOrderList = WorkOrder.objects.filter(
        Q(status__name='等待中') | Q(status__name='加工中'))
    producing = list(
        map(lambda obj: {'key': obj.key, 'bottle': obj.bottle, 'order': obj.order.number, 'LP': positionSelect(obj, '理瓶'), 'SLA': positionSelect(obj, '数粒A'), 'SLB': positionSelect(obj, '数粒B'), 'SLC': positionSelect(obj, '数粒C'), 'XG': positionSelect(obj, '旋盖'), 'CZ': positionSelect(obj, '称重'), 'TB': positionSelect(obj, '贴签'), 'HJ': positionSelect(obj, '桁架'), 'order': obj.order.number}, workOrderList))

    return JsonResponse({'xaxis': list(map(lambda obj: obj.number, Order.objects.all())), 'powerana': powerAna(), 'qualana': qualAna(), 'mateana': mateAna(), 'storeana': storeAna(), 'producing': producing, 'res': os.path.exists(BASE_DIR+'/listen.txt'), 'info': info})
