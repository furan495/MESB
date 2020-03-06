import os
import re
import json
import time
import random
import datetime
import numpy as np
import pandas as pd
from app.utils import *
from app.models import *
from app.serializers import *
from itertools import product
from django.db.models import Q
from django.http import JsonResponse
from django.db.models.aggregates import Count, Sum
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

    route = Order.objects.get(number=params[3]).route
    processList = list(
        map(lambda obj: obj['text'], json.loads(route.data)['nodeDataArray']))

    if position[params[0]] == '理瓶':
        workOrder = WorkOrder.objects.filter(
            Q(description__icontains=color[params[2]], bottle='', status__name='等待中', order=Order.objects.get(number=params[3]))).order_by('createTime')[0]
        bottle = Bottle.objects.filter(
            Q(order__number=params[3], color=color[params[2]]))[0]
        bottle.number = params[1]
        bottle.save()
        workOrder.bottle = params[1]
        workOrder.startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        workOrder.status = WorkOrderStatus.objects.get(name='加工中')
        order = workOrder.order
        order.status = OrderStatus.objects.get(Q(name='加工中'))
        workOrder.save()
        order.save()

    if position[params[0]] == '称重':
        workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], description__icontains=color[params[2]], order=Order.objects.get(number=params[3])))
        product = Product.objects.get(workOrder=workOrder)
        standard = ProductStandard.objects.get(
            Q(name='重量(单位/g)', product=product))
        standard.realValue = float(standard.expectValue)+random.randint(-5, 5)
        if np.abs(standard.realValue-float(standard.expectValue)) <= product.prodType.errorRange:
            standard.result = '1'
            product.result = '1'
        else:
            standard.result = '2'
            product.result = '2'
            product.reason = '重量不足'
        standard.save()
        product.save()

    try:
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
                         Event.objects.filter(Q(bottle=params[1], workOrder__status__name='加工中'))))
    try:
        if len(eventList) == 0 or processList[:len(eventList)] != eventList:
            with open(BASE_DIR+'/listen.txt', 'w') as f:
                f.write('这是一个废瓶')
            workOrder = WorkOrder.objects.get(
                Q(bottle=params[1], order=Order.objects.get(number=params[3])))
            workOrder.status = WorkOrderStatus.objects.get(name='失败')
            workOrder.save()
    except Exception as e:
        with open(BASE_DIR+'/listen.txt', 'w') as f:
            f.write('这是一个废瓶')

    return JsonResponse({'res': 'res'})


@csrf_exempt
def storeOperate(request):
    position = {'CK': '出库', 'RK': '入库'}
    color = {'1': '红瓶', '2': '绿瓶', '3': '蓝瓶'}
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')
    workOrder = WorkOrder.objects.get(
        Q(bottle=params[1], description__icontains=color[params[2]], order__number=params[3]))
    workOrder.status = WorkOrderStatus.objects.get(name='已完成')
    workOrder.endTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    workOrder.save()
    if len(WorkOrder.objects.filter(Q(status__name='等待中', order__number=params[3]))) == 0:
        order = Order.objects.get(number=params[3])
        order.status = OrderStatus.objects.get(name='完成')
        order.save()
    bottle = Bottle.objects.get(
        Q(number=params[1], order__number=params[3], color=color[params[2]]))
    bottle.status = BottleState.objects.get(name='入库')
    bottle.save()
    event = Event()
    event.workOrder = workOrder
    event.bottle = params[1]
    event.source = position[params[0]]
    event.title = '进入%s单元' % position[params[0]]
    event.save()
    product = Product.objects.get(workOrder=workOrder)
    pallet = Pallet.objects.filter(Q(rate__lt=0.67))[0]
    product.pallet = pallet
    product.save()
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
    return JsonResponse({'res': 'res'})


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
        res = {'name': user.name, 'authority': user.role.authority,
               'role': user.role.name, 'phone': user.phone, 'avatar': user.avatar}
    else:
        res = 'err'
    return JsonResponse({'res': res})


@csrf_exempt
def querySelect(request):
    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order' or params['model'] == 'productType':
        selectList = {
            'route': list(map(lambda obj: obj.name, ProcessRoute.objects.all())),
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
            'store': list(map(lambda obj: [obj.name, obj.key], Store.objects.all())),
        }
    if params['model'] == 'tool':
        selectList = {
            'toolType': ['自制', '外采'],
            'store': list(map(lambda obj: [obj.name, obj.key], Store.objects.all())),
        }
    if params['model'] == 'user':
        selectList = {
            'gender': ['男', '女'],
            'role': list(map(lambda obj: obj.name,  Role.objects.all())),
            'department': list(map(lambda obj: obj.name, Department.objects.all()))
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
    order.save()
    for description in orderDesc:
        if len(description.split(',')) > 1:
            for i in range(int(description.split(',')[-1].split(':')[1])):
                workOrder = WorkOrder()
                workOrder.order = order
                workOrder.bottle = ''
                workOrder.endTime = ''
                workOrder.startTime = ''
                time.sleep(0.01)
                workOrder.number = str(time.time()*1000000)
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
                standard.name = '重量(单位/g)'
                standard.expectValue = str(np.sum(list(map(lambda obj: int(obj), re.findall(
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
    with open(BASE_DIR+'/upload/document/'+f.name, 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    document = Document()
    document.up = up
    document.name = f.name
    document.path = 'http://%s:8899/upload/document/%s' % (url, f.name)
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
    with open(BASE_DIR+'/upload/picture/'+f.name, 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    pro.path = 'http://%s:8899/upload/picture/%s' % (url, f.name)
    pro.save()
    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def uploadAvatar(request):
    url = request.POST['url']
    phone = request.POST['phone']
    user = User.objects.get(phone=phone)
    f = request.FILES['file']
    with open(BASE_DIR+'/upload/avatar/%s%s' % (user.name, f.name[f.name.index('.'):]), 'wb') as uf:
        for chunk in f.chunks():
            uf.write(chunk)
    user.avatar = 'http://%s:8899/upload/avatar/%s%s' % (url,
                                                         user.name, f.name[f.name.index('.'):])
    user.save()
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
        position = StroePosition()
        position.store = Store.objects.get(key=params['key'])
        position.number = '%s-%s' % (str(i+1), params['key'])
        position.status = '1'
        position.save()
        pallet = Pallet()
        pallet.position = StroePosition.objects.get(
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
    modelMap = {'order': '订单', 'material': '物料', 'processRoute': '工艺', 'user': '用户', 'role': '角色', 'store': '仓库',
                'workShop': '车间', 'device': '设备', 'document': '文档', 'productStandard': '质检数据', 'bom': 'BOM', 'tool': '工具',
                'productType': '产品', 'productLine': '产线', 'product': '成品', 'workOrder': '工单', 'producing': '生产', 'unqualified': '不合格', 'mateAna': '耗材统计', 'powerAna': '产能报表', 'qualAna': '质量统计'}
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
                '订单类别': obj.orderType.name, '选用工艺': obj.route.name, '订单状态': obj.status.name, '创建人': obj.creator, '订单编号': obj.number,
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

    df = pd.DataFrame(excel)
    df.to_excel(BASE_DIR+'/upload/export/%s报表.xlsx' %
                modelMap[params['model']])
    return JsonResponse({'res': 'http://%s:8899/upload/export/%s报表.xlsx' % (params['url'], modelMap[params['model']])})


@csrf_exempt
def queryPoweranaChart(request):
    data = powerAna()
    return JsonResponse({'res': data, 'xaxis': list(map(lambda obj: obj.number, Order.objects.all()))})


@csrf_exempt
def queryMateanaChart(request):
    data = mateAna()
    return JsonResponse({'res': data})
