import os
import json
import time
import random
import datetime
import numpy as np
from app.utils import *
from app.models import *
from app.serializers import *
from django.db.models import Q, F
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models.aggregates import Count, Sum, Max, Min, Avg

# Create your views here.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@csrf_exempt
def recordWeight(request):
    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')
    print(params)

    try:
        workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], description__icontains=color[params[2]], order=Order.objects.get(number=params[3])))
        product = Product.objects.get(workOrder=workOrder)
        standard = ProductStandard.objects.get(
            Q(name='重量', product=product))
        standard.realValue = float(params[4])
        if np.abs(standard.realValue-float(standard.expectValue)) <= product.prodType.errorRange:
            standard.result = '合格'
            product.result = '合格'
        else:
            standard.result = '不合格'
            product.result = '不合格'
            product.reason = '重量不足'
        standard.save()
        product.save()
    except:
        pass

    return JsonResponse({'res': 'ok'})


@csrf_exempt
def wincc5(request):
    position = {'startB': '出库开始', 'stopB': '出库结束', 'startC': '数控车开始', 'stopC': '数控车结束',
                'startD': '加工中心开始', 'stopD': '加工中心结束', 'startE': '检测包装开始', 'stopE': '检测包装结束', 'check': '质检', 'startF': '入库开始', 'stopF': '入库结束'}
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

    print(params)

    store = Store.objects.get(
        Q(storeType__name='成品库', productLine=WorkOrder.objects.get(number=params[1]).order.line))

    if position[params[0]] == '出库开始':
        workOrder = WorkOrder.objects.get(Q(number=params[1]))
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        workOrder.save()
        order = workOrder.order
        order.status = OrderStatus.objects.get(Q(name='加工中'))
        order.save()
    if position[params[0]] == '质检':
        workOrder = WorkOrder.objects.get(Q(number=params[1]))
        product = workOrder.workOrder
        standard = ProductStandard.objects.get(
            Q(name='外观', product=product))
        if random.random() > 0.5:
            product.result = '合格'
            standard.result = '合格'
            standard.realValue = '合格'
        else:
            product.result = '不合格'
            product.reason = '检测不合格'
            standard.result = '不合格'
            standard.realValue = '不合格'
        product.save()
        standard.save()
    if position[params[0]] == '入库结束':
        workOrder = WorkOrder.objects.get(Q(number=params[1]))
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='已完成')
        workOrder.save()

        product = workOrder.workOrder
        storePosition = StorePosition.objects.get(
            Q(number='%s-%s' % (product.inPos, store.key)))
        storePosition.content = '%s-%s' % (product.name, workOrder.number)
        storePosition.save()

        order = workOrder.order
        if WorkOrder.objects.filter(Q(status__name='加工中', order=order)).count() == 0:
            order.status = OrderStatus.objects.get(Q(name='已完成'))
            order.save()

    event = Event()
    event.workOrder = WorkOrder.objects.get(Q(number=params[1]))
    event.source = position[params[0]]
    event.title = position[params[0]]
    event.save()
    return JsonResponse({'res': 'res'})


@csrf_exempt
def wincc4(request):

    position = {'startA': '3D视觉分拣模块开始', 'stopA': '3D视觉分拣模块结束', 'startB': '数控车模块开始', 'stopB': '数控车模块结束', 'startC': '加工中心模块开始', 'stopC': '加工中心模块结束', 'startD': '精雕机模块开始', 'stopD': '精雕机模块结束', 'startF': '清洗打标模块开始', 'stopF': '清洗打标模块结束',
                'startG': '焊接模块开始', 'stopG': '焊接模块结束', 'startH': '打磨模块开始', 'stopH': '打磨模块结束', 'startF2': '二次清洗开始', 'stopF2': '二次清洗结束', 'startI': '装配模块开始', 'stopI': '装配模块结束', 'check': '质检', 'startJ': '成品库模块开始', 'stopJ': '成品库模块结束'}

    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

    workOrder = WorkOrder.objects.get(Q(number=params[1]))
    if 'start' in params[0]:
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
    if 'stop' in params[0]:
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='已完成')
    if params[0] == 'stopJ':
        product = workOrder.product
        product.status = ProductState.objects.get(name='入库')
        product.save()
        order = product.order
        if order.products.all().filter(Q(status=None)).count() != 0:
            order.status = OrderStatus.objects.get(name='已完成')
            order.save()
    workOrder.save()

    event = Event()
    event.workOrder = workOrder
    event.source = position[params[0]][:-2]
    event.title = position[params[0]]
    event.save()

    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def wincc3(request):

    position = {'startB': 'B模块出库开始', 'stopB': 'B模块出库结束', 'startC': 'C模块加工开始', 'stopC': 'C模块加工结束',
                'startD': 'D模块加工开始', 'stopD': 'D模块加工结束', 'startE': 'E模块加工开始', 'stopE': 'E模块加工结束',
                'startF': 'F模块加工开始', 'stopF': 'F模块加工结束', 'startInB': 'B模块入库开始', 'stopInB': 'B模块入库结束', 'check': '质检', 'error': '失败'}
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

    print(params)

    store = Store.objects.get(
        Q(storeType__name='混合库', productLine=WorkOrder.objects.get(number=params[1]).order.line))

    if position[params[0]] == 'B模块出库开始':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        workOrder.save()
        order = workOrder.order
        order.status = OrderStatus.objects.get(Q(name='加工中'))
        order.save()
    if position[params[0]] == '质检':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        product = workOrder.workOrder
        standard = ProductStandard.objects.get(
            Q(name='外观', product=product))
        if random.random() > 0.5:
            product.result = '合格'
            standard.result = '合格'
            standard.realValue = '合格'
        else:
            product.result = '不合格'
            product.reason = '检测不合格'
            standard.result = '不合格'
            standard.realValue = '不合格'
        product.save()
        standard.save()
    if position[params[0]] == '失败':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.status = WorkOrderStatus.objects.get(name='失败')
        workOrder.save()
    if position[params[0]] == 'B模块入库结束':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='已完成')
        workOrder.save()
        product = workOrder.workOrder
        storePosition = StorePosition.objects.get(
            Q(number='%s-%s' % (product.inPos, store.key)))
        storePosition.save()
        order = workOrder.order
        if WorkOrder.objects.filter(Q(status__name='加工中', order=order)).count() == 0:
            order.status = OrderStatus.objects.get(Q(name='已完成'))
            order.save()

    event = Event()
    event.workOrder = WorkOrder.objects.get(
        Q(number=params[1], order__number=params[2]))
    event.source = position[params[0]]
    event.title = position[params[0]]
    event.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def wincc2(request):
    position = {'startB': 'B模块出库', 'startC': 'C模块加工开始', 'stopC': 'C模块加工结束',
                'startD': 'D模块加工开始', 'stopD': 'D模块加工结束', 'stopB': 'B模块入库', 'check': '质检', 'error': '失败'}
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

    print(params)

    store = Store.objects.get(
        Q(storeType__name='混合库', productLine=WorkOrder.objects.get(number=params[1]).order.line))

    if position[params[0]] == 'B模块出库':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        workOrder.save()
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
            product.result = '合格'
            standard.result = '合格'
            standard.realValue = '合格'
        else:
            product.result = '不合格'
            product.reason = '检测不合格'
            standard.result = '不合格'
            standard.realValue = '不合格'
        product.save()
        standard.save()
    if position[params[0]] == '失败':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.status = WorkOrderStatus.objects.get(name='失败')
        workOrder.save()
    if position[params[0]] == 'B模块入库':
        workOrder = WorkOrder.objects.get(
            Q(number=params[1], order__number=params[2]))
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = WorkOrderStatus.objects.get(name='已完成')
        workOrder.save()
        product = workOrder.workOrder

        storePosition = StorePosition.objects.get(
            Q(number='%s-%s' % (product.inPos, store.key)))
        storePosition.save()

        order = workOrder.order
        if WorkOrder.objects.filter(Q(status__name='加工中', order=order)).count() == 0:
            order.status = OrderStatus.objects.get(Q(name='已完成'))
            order.save()

    event = Event()
    event.workOrder = WorkOrder.objects.get(
        Q(number=params[1], order__number=params[2]))
    event.source = position[params[0]]
    event.title = position[params[0]]
    event.save()
    return JsonResponse({'res': 'res'})


@csrf_exempt
def wincc(request):

    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    position = {'LP': '理瓶', 'XG': '旋盖', 'SLA': '数粒A',
                'SLB': '数粒B', 'SLC': '数粒C', 'CZ': '称重', 'TB': '贴签', 'HJ': '桁架'}
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

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
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')
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
def querySelect(request):
    """ for pos in StorePosition.objects.filter(Q(store__storeType__name='成品库')):
        pos.status='4'
        pos.save()

    for pos in StorePosition.objects.filter(Q(store__storeType__name='原料库')):
        pos.status = '3'
        pos.save() """

    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order' or params['model'] == 'productType':
        selectList = {
            'line': list(map(lambda obj: obj.name, ProductLine.objects.all())),
            'customer': list(map(lambda obj: obj.name, Customer.objects.all())),
            'orderType': list(map(lambda obj: obj.name, OrderType.objects.all())),
            'route': list(map(lambda obj: obj.name, ProcessRoute.objects.filter(~Q(processes__key=None)))),
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
            'direction': ['行优先', '列优先'],
            'origin': ['左上起点', '左下起点'],
            'workShop': list(map(lambda obj: obj.name, WorkShop.objects.all())),
            'storeType': list(map(lambda obj: obj.name, StoreType.objects.all())),
            'material': list(set(map(lambda obj: obj.name, Material.objects.all()))),
            'productLine': list(map(lambda obj: obj.name, ProductLine.objects.all())),
            'product': list(map(lambda obj: obj.name, ProductType.objects.filter(Q(orderType__name=params['order'])))),
        }
    if params['model'] == 'productLine':
        selectList = {
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
            'product': list(map(lambda obj: obj.name, Product.objects.filter(Q(result=1, workOrder__order__orderType__name=params['order'])))),
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


errTime = 0
@csrf_exempt
def queryProducing(request):
    global errTime
    info = ''
    params = json.loads(request.body)
    if os.path.exists(BASE_DIR+'/listen.txt'):
        errTime = errTime+1
        with open(BASE_DIR+'/listen.txt') as f:
            info = f.read()

    if errTime == 3:
        errTime = 0
        if os.path.exists(BASE_DIR+'/listen.txt'):
            os.remove(BASE_DIR+'/listen.txt')

    """ workOrderList = WorkOrder.objects.filter(
        Q(status__name='等待中', order__orderType__name=params['order']) | Q(status__name='加工中', order__orderType__name=params['order'])) """

    productList = Product.objects.filter(
        Q(workOrders__status__name='等待中', order__orderType__name=params['order']) | Q(workOrders__status__name='加工中', order__orderType__name=params['order'])).distinct()

    if params['order'] == '灌装':
        producing = list(
            map(lambda obj: {'key': obj.key, 'bottle': obj.bottle, 'order': obj.order.number, 'LP': positionSelect(obj, '理瓶'), 'SLA': positionSelect(obj, '数粒A'), 'SLB': positionSelect(obj, '数粒B'), 'SLC': positionSelect(obj, '数粒C'), 'XG': positionSelect(obj, '旋盖'), 'CZ': positionSelect(obj, '称重'), 'TB': positionSelect(obj, '贴签'), 'HJ': positionSelect(obj, '桁架')}, workOrderList))
    if params['order'] == '机加':
        """
            河北
            producing = list(
            map(lambda obj: {'key': obj.key, 'workOrder': obj.number, 'startB': positionSelect(obj, 'B模块出库'), 'startC': positionSelect(obj, 'C模块加工开始'), 'stopC': positionSelect(obj, 'C模块加工结束'), 'startD': positionSelect(obj, 'D模块加工开始'), 'stopD': positionSelect(obj, 'D模块加工结束'), 'stopB': positionSelect(obj, 'B模块入库'), 'description': obj.description,'order': obj.order.number}, workOrderList)) """
        # 湖北
        producing = list(
            map(lambda obj: {'key': obj.key, 'name': obj.name, 'startA': positionSelect(obj, '3D视觉分拣模块开始'), 'startB': positionSelect(obj, '数控车模块开始'), 'startC': positionSelect(obj, '加工中心模块开始'), 'startD': positionSelect(obj, '精雕机模块开始'), 'startF': positionSelect(obj, '清洗打标模块开始'), 'startG': positionSelect(obj, '焊接模块开始'), 'startH': positionSelect(obj, '打磨模块开始'), 'startF2': positionSelect(obj, '二次清洗开始'), 'startI': positionSelect(obj, '装配模块开始'), 'startJ': positionSelect(obj, '成品库模块开始'), }, productList))
        """ producing = list(
            map(lambda obj: {'key': obj.key, 'workOrder': obj.number,  'startB': positionSelect(obj, '出库开始'), 'startC': positionSelect(obj, '数控车开始'), 'startD': positionSelect(obj, '加工中心开始'), 'startE': positionSelect(obj, '检测包装开始'), 'startF': positionSelect(obj, '入库开始'), 'stopB': positionSelect(obj, '出库结束'), 'stopC': positionSelect(obj, '数控车结束'), 'stopD': positionSelect(obj, '加工中心结束'), 'stopE': positionSelect(obj, '检测包装结束'), 'stopF': positionSelect(obj, '入库结束')}, workOrderList)) """
    if params['order'] == '电子装配':
        producing = list(
            map(lambda obj: {'key': obj.key, 'workOrder': obj.number+'/'+obj.description, 'startB': positionSelect(obj, 'B模块出库开始'), 'stopB': positionSelect(obj, 'B模块出库结束'), 'startC': positionSelect(obj, 'C模块加工开始'), 'stopC': positionSelect(obj, 'C模块加工结束'), 'startD': positionSelect(obj, 'D模块加工开始'), 'stopD': positionSelect(obj, 'D模块加工结束'), 'startE': positionSelect(obj, 'E模块加工开始'), 'stopE': positionSelect(obj, 'E模块加工结束'), 'startF': positionSelect(obj, 'F模块加工开始'), 'stopF': positionSelect(obj, 'F模块加工结束'), 'startInB': positionSelect(obj, 'B模块入库开始'), 'stopInB': positionSelect(obj, 'B模块入库结束')}, workOrderList))

    return JsonResponse({'producing': producing, 'res': os.path.exists(BASE_DIR+'/listen.txt'), 'info': info})


@csrf_exempt
def queryCharts(request):
    params = json.loads(request.body)
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
    stop = datetime.datetime.strptime(
        params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
    data = Product.objects.filter(Q(order__orderType__name=params['order'])).values('batch').annotate(reals=Count('batch', filter=Q(workOrders__status__name='已完成')), expects=Count(
        'batch'), good=Count('result', filter=Q(result='合格')), bad=Count('result', filter=Q(result='不合格'))).values('batch', 'good', 'bad', 'expects', 'reals')

    goodRate = list(
        map(lambda obj: [dataX(obj['batch']), round(rateY(obj), 2)], data))

    categories = list(Product.objects.all().values_list(
        'batch', flat=True).distinct())

    if Product.objects.all().count() == 0:
        start = '%s-%s-%s' % (str(year), str(month-1 if day <
                                             14 else month), str(np.abs(day-14)))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000, time.time()*1000, 24*60*60*1000):
            goodRate.append([day+8*60*60*1000, round(random.random(), 2)])
            categories.append(time.strftime(
                '%m-%d', time.localtime(day/1000)))

    progress = list(map(lambda obj: {'key': obj.key, 'number': obj.number, 'progress': round(obj.workOrders.all().filter(Q(status__name='已完成')).count(
    )/(obj.workOrders.all().count()), 2)}, Product.objects.filter(Q(workOrders__status__name='加工中') | Q(workOrders__status__name='等待中')).distinct()))

    if Product.objects.filter(Q(workOrders__status__name='加工中') | Q(workOrders__status__name='等待中')).count() == 0:
        for i in range(10):
            progress.append({'key': i, 'number': '产品%s' % (str(i+1)),
                             'progress': random.randint(0, 100)})

    rate = [
        {'name': '合格率', 'type': 'areaspline',
            'color': 'rgb(190,147,255)', 'data': goodRate},
    ]

    target = Product.objects.filter(
        Q(batch__gte=datetime.datetime.now().date())).count()

    current = Product.objects.filter(
        Q(batch__gte=datetime.datetime.now().date(), status__name='入库')).count()

    good = Product.objects.filter(
        Q(batch__gte=datetime.datetime.now().date(), result='合格')).count()

    power = {'target': target if target != 0 else 100, 'current': current if current != 0 else 0, 'good': good if good != 0 else 0,
             'series': [{'data': [{'y':  current if current != 0 else 0, 'target': target if target != 0 else 100}]}]}

    return JsonResponse({'progress': progress, 'categories': categories, 'mateana': storeAna(params['order']), 'quality': qualityChart(params['order'], start, stop, all=True), 'goodRate': rate, 'power': power})


@csrf_exempt
def deviceState(request):
    states = {'device': 3, 'user': 'x1,y1,z1',
              'tool': 'x2,y2,z2', 'angle': 'J1,J2,J3,J4,J5,J6'}
    name = ''
    for key, val in zip(states.keys(), states.values()):
        name += '%s:%s;' % (key, val)
    state = DeviceState()
    state.device = Device.objects.get(key=states['device'])
    state.name = name
    state.save()
    return JsonResponse({'res': 'ok'})
