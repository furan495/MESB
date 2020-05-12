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
from django.apps import apps
from functools import reduce
from app.serializers import *
from itertools import product
from django.db.models import Q, F
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
def queryStores(request):
    params = json.loads(request.body)
    gz = Store.objects.filter(
        Q(storeType__name=params['type'], workShop__name=params['shop'], productLine__name=params['line'])).count()
    mw = Store.objects.filter(
        Q(storeType__name=params['type'], workShop__name=params['shop'], productLine__name=params['line'])).count()
    return JsonResponse({'gz': gz, 'mw': mw})


@csrf_exempt
def wincc2(request):
    title = {'startB': 'B模块出库', 'startC': 'C模块加工开始', 'stopC': 'C模块加工结束',
             'startD': 'D模块加工开始', 'stopD': 'D模块加工结束', 'stopB': 'B模块入库', 'check': '质检'}
    position = {'startB': 'B出库', 'startC': 'C加工开始', 'stopC': 'C加工结束',
                'startD': 'D加工开始', 'stopD': 'D加工结束', 'stopB': 'B入库', 'check': '质检', 'error': '失败'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')

    print(params)

    store = Store.objects.get(
        Q(storeType__name='混合库', productLine=WorkOrder.objects.get(number=params[1]).order.line))

    if position[params[0]] == 'B出库':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        workOrder.save()
        storePosition = StorePosition.objects.get(
            Q(number='%s-%s' % (workOrder.workOrder.outPos, store.key)))
        storePosition.status = '4'
        storePosition.save()
        order = workOrder.order
        order.status = OrderStatus.objects.get(Q(name='加工中'))
        order.save()
        Material.objects.filter(Q(store=store))[0].delete()
    if position[params[0]] == '质检':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        product = workOrder.workOrder
        standard = ProductStandard.objects.get(
            Q(name='外观', product=product))
        if random.random() > 0.5:
            product.result = '1'
            standard.result = '1'
            standard.realValue = '合格'
        else:
            product.result = '2'
            product.reason = '检测不合格'
            standard.result = '2'
            standard.realValue = '不合格'
        product.save()
        standard.save()
    if position[params[0]] == '失败':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.status = WorkOrderStatus.objects.get(name='失败')
        workOrder.save()
    if position[params[0]] == 'B入库':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='已完成')
        workOrder.save()
        product = workOrder.workOrder
        storePosition = StorePosition.objects.get(
            Q(number='%s-%s' % (workOrder.workOrder.inPos, store.key)))
        storePosition.status = '3'
        storePosition.content = '%s-%s' % (product.name,
                                           product.workOrder.number)
        storePosition.save()

        order = workOrder.order
        if WorkOrder.objects.filter(Q(status__name='加工中', order=order)).count() == 0:
            order.status = OrderStatus.objects.get(Q(name='已完成'))
            order.save()

    event = Event()
    event.workOrder = WorkOrder.objects.get(
        Q(number=params[1], order__number=params[2]))
    event.source = position[params[0]]
    event.title = title[params[0]]
    event.save()
    return JsonResponse({'res': 'res'})


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
    store = Store.objects.get(
        Q(storeType__name='成品库', productLine=Order.objects.get(number=params[1]).line))
    storePosition = StorePosition.objects.get(
        Q(number='%s-%s' % (params[-1], store.key)))
    storePosition.status = '3'
    storePosition.save()
    pallet = Pallet.objects.get(
        Q(number=params[-2], position__store=store))
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
def queryMWPosition(request):
    params = json.loads(request.body)
    mwPosition = StorePosition.objects.get(
        number=params['item'].split('/')[0]).content
    return JsonResponse({'res': mwPosition})


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
        res = {'name': user.name, 'authority': user.role.authority, 'key': user.key, 'status': user.status,
               'role': user.role.name, 'phone': user.phone}
    else:
        res = 'err'
    return JsonResponse({'res': res, 'count': User.objects.filter(Q(status='2')).count(), })


@csrf_exempt
def updateUserState(request):
    params = json.loads(request.body)
    user = User.objects.get(key=params['key'])
    user.status = params['status']
    user.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def logoutUser(request):
    params = json.loads(request.body)
    user = User.objects.get(
        Q(phone=params['phone'], password=params['password']))
    user.status = '1'
    user.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def logout(request):
    params = json.loads(request.body)
    print(params)
    """ user = User.objects.get(
        Q(phone=params['phone'], password=params['password']))
    user.status = '1'
    user.save() """
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def checkUserState(request):
    params = json.loads(request.body)
    res = ''
    try:
        user = User.objects.get(key=params['key'])
        res = user.status
    except:
        pass
    return JsonResponse({'res': res, 'count': User.objects.filter(Q(status='2')).count()})


@csrf_exempt
def queryInterviewChart(request):
    data = list(map(lambda obj: [dataX(obj.time.date()), dataY(obj.time)], Operate.objects.filter(
        Q(name='登陆系统')).order_by('time')))
    return JsonResponse({'res': reduce(lambda x, y: x if y in x else x+[y], [[], ]+data)})


@csrf_exempt
def updateDataView(request):
    params = json.loads(request.body)
    product = ProductType.objects.filter(
        Q(orderType__name=params['orderType']))
    productDict, fieldDict, materialStr = {}, {}, ''
    for field in apps.get_model('app', 'Bottle')._meta.fields:
        fieldDict[field.verbose_name] = field.name
    for prod in product:
        productDict[prod.name] = Count('workOrders__workOrder__name', filter=Q(
            workOrders__workOrder__name=prod.name)) if params['orderType'] != '灌装' else Count('bottles', filter=Q(bottles__color=prod.name))
        if params['orderType'] == '灌装':
            boms = BOMContent.objects.filter(
                Q(bom__product=prod) & ~Q(material__icontains=prod.name) & ~Q(material__icontains='盖'))
            for bom in boms:
                materialStr = materialStr+bom.material.split('/')[0]+','
            for mat in list(filter(lambda obj: obj != '', list(set(materialStr.split(','))))):
                productDict[prod.name+mat] = Avg(
                    'bottles__%s' % fieldDict[mat], filter=Q(bottles__color=prod.name))

    orders = Order.objects.filter(
        Q(status=OrderStatus.objects.get(name='已排产'), orderType=OrderType.objects.get(name=params['orderType']))).values('number').annotate(订单编号=F('number'), 订单批次=F('batch'), 排产时间=F('scheduling'), 订单状态=F('status__name'),  **productDict).values('订单编号', '订单批次', '排产时间', '订单状态', *productDict.keys())

    dv = DataView.objects.all()[0]
    if params['orderType'] != '机加':
        dv.mwContent = formatSql(orders.query.__str__().split(' '))
    if params['orderType'] == '电子装配':
        dv.eaContent = formatSql(orders.query.__str__().split(' '))
    if params['orderType'] == '灌装':
        dv.gzContent = formatSql(orders.query.__str__().split(' '))
    dv.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def querySelect(request):
    """ data = Order.objects.filter(Q(status__name='已完成',orderType__name='灌装')).values('number').annotate(
        rbot=Count('bottles', filter=Q(bottles__color='红瓶')),
        rred=Avg('bottles__red', filter=Q(bottles__color='红瓶')),
        rgreen=Avg('bottles__green', filter=Q(bottles__color='红瓶')),
        rblue=Avg('bottles__blue', filter=Q(bottles__color='红瓶')),
        gbot=Count('bottles', filter=Q(bottles__color='绿瓶')),
        gred=Avg('bottles__red', filter=Q(bottles__color='绿瓶')),
        ggreen=Avg('bottles__green', filter=Q(bottles__color='绿瓶')),
        gblue=Avg('bottles__blue', filter=Q(bottles__color='绿瓶')),
        bbot=Count('bottles', filter=Q(bottles__color='蓝瓶')),
        bred=Avg('bottles__red', filter=Q(bottles__color='蓝瓶')),
        bgreen=Avg('bottles__green', filter=Q(bottles__color='蓝瓶')),
        bblue=Avg('bottles__blue', filter=Q(bottles__color='蓝瓶')),
    ).values('number',  'rbot', 'rred', 'rgreen', 'rblue', 'gbot', 'gred', 'ggreen', 'gblue', 'bbot', 'bred', 'bgreen', 'bblue', 'scheduling', 'status__name',) """

    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order' or params['model'] == 'productType':
        selectList = {
            'line': list(map(lambda obj: obj.name, ProductLine.objects.all())),
            'route': list(map(lambda obj: obj.name, ProcessRoute.objects.all())),
            'customer': list(map(lambda obj: obj.name, Customer.objects.all())),
            'orderType': list(map(lambda obj: obj.name, OrderType.objects.all())),
            'product': list(map(lambda obj: [obj.name, obj.orderType.name], ProductType.objects.filter(~Q(bom__contents__key=None))))
        }
    if params['model'] == 'bom':
        selectList = {
            'materials': list(set(map(lambda obj: obj.name+'/'+obj.size, Material.objects.all()))),
            'product': list(map(lambda obj: obj.name, ProductType.objects.filter(Q(bom=None)))),
        }
    if params['model'] == 'processRoute':
        selectList = {
            'routeType': list(map(lambda obj: obj.name, OrderType.objects.all())),
        }
    if params['model'] == 'store':
        selectList = {
            'workShop': list(map(lambda obj: obj.name, WorkShop.objects.all())),
            'storeType': list(map(lambda obj: obj.name, StoreType.objects.all())),
            'productLine': list(map(lambda obj: obj.name, ProductLine.objects.all())),
        }
    if params['model'] == 'productLine':
        selectList = {
            'state': list(map(lambda obj: obj.name, LineState.objects.all())),
            'workShop': list(map(lambda obj: obj.name, WorkShop.objects.all())),
            'lineType': list(map(lambda obj: obj.name, OrderType.objects.all())),
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
    if params['model'] == 'user':
        selectList = {
            'gender': ['男', '女'],
            'role': list(map(lambda obj: obj.name,  Role.objects.all())),
            'department': list(map(lambda obj: obj.name, Organization.objects.filter(~Q(parent=None))))
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
def deleteOrganization(request):
    params = json.loads(request.body)
    organization = Organization.objects.get(key=params['key'])
    if organization.parent:
        Organization.objects.filter(Q(key=params['key']) | Q(
            parent=organization.name)).delete()
    else:
        Organization.objects.all().delete()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def orderSplit(request):
    params = json.loads(request.body)
    orderDesc = params['description'].split(';')
    order = Order.objects.get(key=params['key'])
    order.status = OrderStatus.objects.get(name='已排产')
    order.batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order.scheduling = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order.save()
    if params['orderType'] == '灌装':
        for description in orderDesc:
            if len(description.split(',')) > 1:
                for i in range(int(description.split(',')[-1].split(':')[1])):
                    workOrder = WorkOrder()
                    workOrder.order = order
                    time.sleep(0.1)
                    workOrder.number = str(time.time()*1000000)[:15]
                    workOrder.status = WorkOrderStatus.objects.get(name='等待中')
                    workOrder.description = ','.join(
                        description.split(',')[:4])
                    workOrder.save()

                    product = Product()
                    product.name = workOrder.description.split(',')[
                        0].split(':')[1]
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
    else:
        for description in orderDesc:
            if len(description.split('x')) > 1:
                for i in range(int(description.split('x')[1])):
                    workOrder = WorkOrder()
                    workOrder.order = order
                    time.sleep(0.1)
                    workOrder.number = random.randint(0, 255)
                    workOrder.status = WorkOrderStatus.objects.get(name='等待中')
                    workOrder.description = description.split('x')[0]
                    workOrder.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def bandProduct(request):
    params = json.loads(request.body)
    workOrder = WorkOrder.objects.filter(
        Q(order__number=params['number']))
    outPos = list(StorePosition.objects.filter(
        Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='3', description__icontains='原料')))[:workOrder.count()]
    outPosition = list(map(lambda obj: obj.number.split('-')[0], outPos))
    inPos = list(StorePosition.objects.filter(
        Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='4', description__icontains='成品')).order_by('-key'))[:workOrder.count()]
    inPosition = list(map(lambda obj: obj.number.split('-')[0], inPos))

    eaOutPosition, eaInPosition = {}, {}

    for i in range(workOrder.count()):
        if params['orderType'] == '电子装配':
            for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                eaOutPosition[pro.name] = StorePosition.objects.filter(
                    Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name))
                eaInPosition[pro.name] = StorePosition.objects.filter(
                    Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name))
        product = Product()
        product.name = workOrder[i].description
        product.number = str(time.time()*1000000)
        product.workOrder = workOrder[i]
        product.outPos = outPosition[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0].number.split(
            '-')[0]
        product.inPos = inPosition[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0].number.split(
            '-')[0]
        product.prodType = ProductType.objects.get(
            Q(orderType__name=params['orderType'], name__icontains=workOrder[i].description.split('x')[0]))
        product.save()

        outP = outPos[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0]
        outP.status = '4'
        outP.save()
        inP = inPos[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0]
        inP.status = '3'
        inP.save()

        standard = ProductStandard()
        standard.name = '外观'
        standard.expectValue = '合格'
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
def deviceUnband(request):
    params = json.loads(request.body)
    for device in Device.objects.filter(Q(process__name=params['process'], process__route__key=params['route'])):
        device.process = None
        device.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def deviceBand(request):
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
    store = Store.objects.get(key=params['key'])
    storeType = store.productLine.lineType.name
    store.direction = params['direction']
    store.dimensions = params['dimensions']
    store.save()
    count = params['row']*params['column']
    if storeType == '电子装配':
        left = np.arange(
            0, count/2).reshape(params['row'], int(params['column']/2))
        right = np.arange(
            count/2, count).reshape(params['row'], int(params['column']/2))
        martix = np.hstack((left, right)).reshape(1, count)
        for i in np.ravel(martix):
            position = StorePosition()
            position.store = Store.objects.get(key=params['key'])
            position.number = '%s-%s' % (str(int(i)+1), params['key'])
            position.status = selectStatus(storeType, i, count)
            position.description = selectDescription(
                storeType, i, count, params['row'], params['column'])
            position.save()
    else:
        for i in range(count):
            position = StorePosition()
            position.store = Store.objects.get(key=params['key'])
            position.number = '%s-%s' % (str(i+1), params['key'])
            position.status = selectStatus(storeType, i, count)
            position.description = selectDescription(
                storeType, i, count, params['row'], params['column'])
            position.save()
            if storeType == '灌装':
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

    series = []
    data = [{'data': series}]
    operateList = Operate.objects.all().order_by('-time')
    for i in range(len(operateList) if len(operateList) <= 100 else 100):
        ope = {}
        ope['value'] = 1
        ope['x'] = dikaer[i][0]
        ope['y'] = dikaer[i][1]
        ope['operate'] = operateList[i].name
        ope['operator'] = operateList[i].operator
        ope['time'] = operateList[i].time.strftime('%Y-%m-%d %H:%M:%S')
        series.append(ope)

    return JsonResponse({'res': data})


@csrf_exempt
def queryQualanaChart(request):
    params = json.loads(request.body)
    orderType = params['order']
    data = qualAna(orderType, all=False)
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
                '产线名称': obj.name, '产线类别': obj.lineType, '隶属车间': obj.workShop.name, '产线编号': obj.number, '产线状态': obj.state.name, '产线描述': obj.description}, ProductLine.objects.all())
        )
    if params['model'] == 'processRoute':
        excel = list(
            map(lambda obj: {
                '工艺名称': obj.name, '工艺类别': obj.routeType, '工艺描述': obj.description, '创建人': obj.creator, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'),
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
                '仓库名称': obj.name, '隶属车间': obj.workShop.name, '使用产线': obj.productLine.name,  '仓库编号': obj.number, '仓库类型': obj.storeType.name, '仓库规模': obj.dimensions},
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
    params = json.loads(request.body)
    data = powerAna(params['order'], all=False)
    return JsonResponse({'res': data})


@csrf_exempt
def queryMateanaChart(request):
    params = json.loads(request.body)
    data = mateAna(params['order'], all=False)
    return JsonResponse({'res': data})


@csrf_exempt
def filterChart(request):
    data = []
    params = json.loads(request.body)
    start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
    stop = datetime.datetime.strptime(
        params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
    if params['chart'] == 'power':
        data = Product.objects.filter(Q(workOrder__order__orderType__name=params['order'], workOrder__order__createTime__gte=start, workOrder__order__createTime__lte=stop)).values('batch').annotate(reals=Count('batch', filter=Q(
            workOrder__status__name='已完成')), expects=Count('batch'), good=Count('result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad', 'expects', 'reals')
        expectData = list(
            map(lambda obj: [dataX(obj['batch']), obj['expects']], data))
        realData = list(
            map(lambda obj: [dataX(obj['batch']), obj['reals']], data))
        goodRate = list(
            map(lambda obj: [dataX(obj['batch']), rateY(obj)], data))
        data = [
            {'name': '预期产量', 'type': 'column', 'data': expectData},
            {'name': '实际产量', 'type': 'column', 'data': realData},
            {'name': '合格率', 'type': 'line', 'yAxis': 1, 'data': goodRate},
        ]
    if params['chart'] == 'qual':
        product = Product.objects.filter(Q(workOrder__order__orderType__name=params['order'], workOrder__order__createTime__gte=start, workOrder__order__createTime__lte=stop)).values(
            'batch').annotate(good=Count('result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
        goodData = list(
            map(lambda obj: [dataX(obj['batch']), obj['good']], product))
        badData = list(
            map(lambda obj: [dataX(obj['batch']), obj['bad']], product))
        reasonData = list(
            map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
                Product.objects.filter(
                    Q(result='2', workOrder__order__orderType__name='灌装'))
                .values('reason')
                .annotate(count=Count('reason'))
                .values('reason', 'count'))
        )
        if params['order'] == '机加':
            data = [
                {'name': '合格', 'type': 'column', 'data': goodData},
                {'name': '不合格', 'type': 'column', 'data': badData},
            ]
        else:
            data = [
                {'name': '合格', 'type': 'column', 'data': goodData},
                {'name': '不合格', 'type': 'column', 'data': badData},
                {'name': '原因汇总', 'type': 'pie', 'color': '#00C1FF', 'data': reasonData, 'innerSize': '50%',
                 'center': [150, 80], 'size':200}
            ]
    if params['chart'] == 'mate':
        redBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='红瓶', order__createTime__gte=start, order__createTime__lte=stop)).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        greenBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='绿瓶', order__createTime__gte=start, order__createTime__lte=stop)).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        blueBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='蓝瓶', order__createTime__gte=start, order__createTime__lte=stop)).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        cap = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(order__createTime__gte=start, order__createTime__lte=stop)).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        red = list(
            map(lambda obj: [dataX(obj['createTime']), obj['reds']],
                Bottle.objects.filter(Q(order__createTime__gte=start, order__createTime__lte=stop)).values('createTime', 'order', 'red').annotate(
                    reds=Sum('red')).values('createTime', 'reds').annotate(count=Count('red')).values('createTime', 'reds')
                ))
        green = list(
            map(lambda obj: [dataX(obj['createTime']), obj['greens']],
                Bottle.objects.filter(Q(order__createTime__gte=start, order__createTime__lte=stop)).values('createTime', 'order', 'green').annotate(
                    greens=Sum('green')).values('createTime', 'greens').annotate(count=Count('green')).values('createTime', 'greens')
                ))
        blue = list(
            map(lambda obj: [dataX(obj['createTime']), obj['blues']],
                Bottle.objects.filter(Q(order__createTime__gte=start, order__createTime__lte=stop)).values('createTime', 'order', 'blue').annotate(
                    blues=Sum('blue')).values('createTime', 'blues').annotate(count=Count('blue')).values('createTime', 'blues')
                ))
        data = [
            {'name': '红粒', 'type': 'column', 'data': red},
            {'name': '红瓶', 'type': 'column', 'data': redBottle},
            {'name': '绿粒', 'type': 'column',  'data': green},
            {'name': '绿瓶', 'type': 'column', 'data': greenBottle},
            {'name': '蓝粒', 'type': 'column',  'data': blue},
            {'name': '蓝瓶', 'type': 'column', 'data': blueBottle},
            {'name': '瓶盖', 'type': 'areaspline', 'data': cap},
        ]
    return JsonResponse({'res': data})


@csrf_exempt
def splitCheck(request):
    params = json.loads(request.body)
    res, info = 'ok', ''
    line = ProductLine.objects.get(name=params['line'])
    route = ProcessRoute.objects.get(name=params['route'])
    if params['orderType'] == line.lineType.name and params['orderType'] == route.routeType.name:
        if params['orderType'] == '灌装':
            particles = {}
            fieldDict = {}
            descriptions = params['description'].split(';')[:-1]
            for field in apps.get_model('app', 'Bottle')._meta.fields:
                fieldDict[field.verbose_name] = field.name
            for desc in descriptions:
                count = desc.split(',')[-1].split(':')[1]
                bottle = desc.split(',')[0].split(':')[1]
                try:
                    occupyBot = Bottle.objects.filter(
                        Q(color=bottle, order__status__name='已排产', order__orderType__name='灌装')).count()
                except:
                    occupyBot = 0
                if Material.objects.filter(Q(name=bottle)).count()-occupyBot < int(count):
                    res = 'err'
                    info = '%s不足，无法排产' % bottle
                for particle in desc.split(',')[1:-1]:
                    particles[particle.split(':')[0]] = Sum(
                        'bottles__%s' % fieldDict[particle.split(':')[0]])
                particleCounts = Order.objects.filter(key=params['key']).annotate(
                    **particles).values(*particles.keys())
                for parti in particleCounts[0].keys():
                    try:
                        occupyPar = Order.objects.filter(Q(status__name='已排产', order__orderType__name='灌装')).annotate(counts=Sum(
                            'bottles__%s' % fieldDict[particle.split(':')[0]])).values('counts')[0]['counts']
                    except:
                        occupyPar = 0
                    if Material.objects.filter(Q(name=parti)).count()-occupyPar < particleCounts[0][parti]:
                        res = 'err'
                        info = '%s不足，无法排产' % parti
        if params['orderType'] == '机加':
            count = 0
            descriptions = params['description']
            for desc in descriptions.split(';')[:-1]:
                count = count+int(desc.split('x')[1])
            occupy = WorkOrder.objects.filter(
                Q(order__status__name='已排产', order__orderType__name='机加')).count()
            if StorePosition.objects.filter(
                    Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='3', description='原料')).count() < count or Material.objects.filter(Q(store__storeType__name='混合库', store__productLine__lineType__name=params['orderType'])).count()-occupy < count:
                res = 'err'
                info = '原料不足，无法排产'
        if params['orderType'] == '电子装配':
            eaOutPosition, eaInPosition = {}, {}
            for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                eaOutPosition[pro.name] = StorePosition.objects.filter(
                    Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name)).count()
                eaInPosition[pro.name] = StorePosition.objects.filter(
                    Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name)).count()
            descriptions = params['description']
            materialStr, materialDict = '', {}
            for desc in descriptions.split(';')[:-1]:
                product = desc.split('x')[0]
                productCount = desc.split('x')[1]
                bom = BOM.objects.get(Q(product__name=product))
                materialStr = materialStr + ','.join(list(map(lambda obj: obj.material, bom.contents.all())))+','
                if eaOutPosition[product]<int(productCount):
                    res = 'err'
                    info = '%s原料底座不足，无法排产' % product
                if eaInPosition[product]<int(productCount):
                    res = 'err'
                    info = '%s成品仓位不足，无法排产' % product
            for material in list(set(materialStr.split(',')))[1:]:
                materialDict[material] = 0
            for desc in descriptions.split(';')[:-1]:
                count = desc.split('x')[1]
                product = desc.split('x')[0]
                bom = BOM.objects.get(Q(product__name=product))
                for mat in bom.contents.all():
                    materialDict[mat.material] = materialDict[mat.material] +  mat.counts*int(count)
            for mat in list(set(materialStr.split(',')))[1:]:
                try:
                    bomContents = BOMContent.objects.filter(
                        Q(bom__product__products__workOrder__order__status__name='已排产', bom__product__products__workOrder__order__orderType__name='电子装配')).values('material').distinct().annotate(counts=Sum('counts', filter=Q(material=mat))).values('counts')
                    occupy = list(filter(lambda obj: obj['counts'] != None, bomContents))[
                        0]['counts']
                except:
                    occupy = 0
                if Material.objects.filter(Q(name=mat.split('/')[0], size=mat.split('/')[1])).count()-occupy < materialDict[mat]:
                    res = 'err'
                    info = '%s不足，无法排产' % mat
        else:
            pass
    else:
        res = 'err'
        info = '产线或工艺不符，无法排产'

    return JsonResponse({'res': res, 'info': info})


@csrf_exempt
def queryOrganization(request):

    data = list(map(lambda obj: {
        'key': obj.key,
        'title': obj.name,
        'children': loopOrganization(obj.name)
    }, Organization.objects.filter(Q(parent=None))))

    series = list(map(lambda obj: [obj.parent if obj.parent else obj.name, obj.name],
                      Organization.objects.filter(~Q(parent=None))))

    return JsonResponse({'tree': data, 'series': series, 'parent': list(map(lambda obj: [obj.key, obj.name], Organization.objects.all()))})


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
        map(lambda obj: {'key': obj.key, 'workOrder': obj.number, 'startB': positionSelect(obj, 'B出库'), 'startC': positionSelect(obj, 'C加工开始'), 'stopC': positionSelect(obj, 'C加工结束'), 'startD': positionSelect(obj, 'D加工开始'), 'stopD': positionSelect(obj, 'D加工结束'), 'stopB': positionSelect(obj, 'B入库'), 'description': obj.description, 'bottle': obj.bottle, 'orderType': obj.order.orderType.name, 'order': obj.order.number, 'LP': positionSelect(obj, '理瓶'), 'SLA': positionSelect(obj, '数粒A'), 'SLB': positionSelect(obj, '数粒B'), 'SLC': positionSelect(obj, '数粒C'), 'XG': positionSelect(obj, '旋盖'), 'CZ': positionSelect(obj, '称重'), 'TB': positionSelect(obj, '贴签'), 'HJ': positionSelect(obj, '桁架'), 'name': obj.number, 'data': [obj.events.count()], 'order': obj.order.number}, workOrderList))
    try:
        route = workOrderList[0].order.route
        processList = list(
            map(lambda obj: obj['text'], json.loads(route.data)['nodeDataArray']))
        order = workOrderList[0].order.number[-4:]
    except:
        processList = []
        order = ''

    return JsonResponse({'producing': producing, 'res': os.path.exists(BASE_DIR+'/listen.txt'), 'processes': processList, 'order': order, 'info': info})


@csrf_exempt
def queryCharts(request):
    params = json.loads(request.body)
    data = Product.objects.filter(Q(workOrder__order__orderType__name=params['order'])).values('batch').annotate(reals=Count('batch', filter=Q(workOrder__status__name='已完成')), expects=Count(
        'batch'), good=Count('result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad', 'expects', 'reals')

    goodRate = list(
        map(lambda obj: [dataX(obj['batch']), round(rateY(obj), 2)], data))
    badRate = list(
        map(lambda obj: [dataX(obj['batch']), round(1-rateY(obj), 2)], data))

    rate = [
        {'name': '合格率', 'type': 'areaspline',
            'color': {
                'linearGradient': {
                    'x1': 0,
                    'y1': 0,
                    'x2': 0,
                    'y2': 1
                },
                'stops': [
                    [0, 'rgba(24,144,255,1)'],
                    [1, 'rgba(24,144,255,0)']
                ]
            }, 'data': goodRate[-20:]},
        {'name': '不合格率', 'type': 'areaspline',
            'color': {
                'linearGradient': {
                    'x1': 0,
                    'y1': 0,
                    'x2': 0,
                    'y2': 1
                },
                'stops': [
                    [0, 'rgba(255,77,79,1)'],
                    [1, 'rgba(255,77,79,0)']
                ]
            }, 'data': badRate[-20:]}
    ]

    times = [
        {'name': '生产耗时', 'type': 'column', 'color': {
                 'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                 'stops': [
                     [0, 'rgba(244,144,255,0)'],
                     [1, 'rgba(244,144,255,1)']
                 ]
        }, 'data': list(
            map(lambda obj: [obj.number[-4:], round((dataX(obj.endTime)-dataX(obj.startTime))/60000, 2)], list(WorkOrder.objects.filter(Q(order__orderType__name=params['order'], status__name='已完成')))[-20:]))}
    ]

    if params['order'] == '灌装':
        product = [{'type': 'pie', 'innerSize': '80%', 'name': '产品占比', 'data': [
            {'name': '红瓶', 'y': Product.objects.filter(
                Q(name__icontains='红瓶')).count()},
            {'name': '绿瓶', 'y':  Product.objects.filter(
                Q(name__icontains='绿瓶')).count()},
            {'name': '蓝瓶', 'y':  Product.objects.filter(
                Q(name__icontains='蓝瓶')).count()},
        ]}]
        position = list(
            map(lambda obj: [obj.rate*100, obj.number], Pallet.objects.all()))
    else:
        product = [
            {'type': 'pie', 'innerSize': '80%', 'name': '产品占比', 'data':
             list(map(lambda obj:
                      {'name': obj.name, 'y': Product.objects.filter(
                          Q(name__icontains=obj.name)).count()},
                      ProductType.objects.filter(Q(orderType__name=params['order']))
                      ))}
        ]
        position = list(map(lambda obj: [obj.status, obj.number], StorePosition.objects.filter(
            Q(store__storeType__name='混合库',store__productLine__lineType__name=params['order']))))

    return JsonResponse({'position': position, 'material': storeAna(params['order']), 'times': times, 'product': product, 'qualana': qualAna(params['order'], all=True), 'mateana': mateAna(params['order'], all=False), 'goodRate': rate, 'power': powerAna(params['order'], all=True)})


@csrf_exempt
def addMaterialOrTool(request):
    params = json.loads(request.body)
    Material.objects.filter(Q(name=None)).delete()
    Tool.objects.filter(Q(name=None)).delete()
    if params['model'] == 'material':
        for i in range(params['addCount']):
            material = Material()
            material.name = params['name']
            material.size = params['size']
            material.unit = params['unit']
            material.mateType = '1' if params['mateType'] == '自制' else '2'
            material.store = Store.objects.get(name=params['store__name'])
            material.save()
    if params['model'] == 'tool':
        for i in range(params['addCount']):
            tool = Tool()
            tool.name = params['name']
            tool.size = params['size']
            tool.unit = params['unit']
            tool.toolType = '1' if params['toolType'] == '自制' else '2'
            tool.store = Store.objects.get(name=params['store__name'])
            tool.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def positionGroup(request):
    params = json.loads(request.body)
    position = StorePosition.objects.get(
        Q(number=params['item'].split('/')[0]))
    position.description = params['value']
    position.save()
    return JsonResponse({'res': 'ok'})


@csrf_exempt
def processParamsSetting(request):
    params = json.loads(request.body)
    processParam = ProcessParams()
    processParam.name = params['name']
    processParam.value = params['value']
    processParam.tagName = params['tagName']
    processParam.topLimit = params['topLimit']
    processParam.lowLimit = params['lowLimit']
    processParam.unit = '' if params['unit'] == '无' else params['unit']
    processParam.process = Process.objects.get(
        Q(name=params['process'], route__key=params['route']))
    processParam.save()
    return JsonResponse({'res': 'ok'})
