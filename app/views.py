import os
import re
import json
import time
import random
import datetime
import numpy as np
import pandas as pd
from app.models import *
from itertools import product
from django.db.models import Q
from django.http import JsonResponse
from django.db.models.aggregates import Count
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
            Q(description__icontains=color[params[2]], bottle='', order=Order.objects.get(number=params[3]))).order_by('createTime')[0]
        workOrder.bottle = params[1]
        workOrder.startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        workOrder.status = WorkOrderStatus.objects.get(key=2)
        workOrder.save()

    if position[params[0]] == '称重':
        workOrder = WorkOrder.objects.get(
            Q(bottle=params[1], order=Order.objects.get(number=params[3])))
        product = Product.objects.get(workOrder=workOrder)
        standard = ProductStandard.objects.get(
            Q(name='重量(单位/g)', product=product))
        err = random.randint(-2, 2)
        standard.realValue = str(float(standard.expectValue)+err)
        if err >= 0:
            standard.result = '1'
            product.prodType = ProductType.objects.get(key=1)
        else:
            standard.result = '2'
            product.prodType = ProductType.objects.get(key=2)
            product.reason = '重量不足'
        standard.save()
        product.save()

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
    params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',')
    workOrder = WorkOrder.objects.get(
        Q(bottle=params[1], order=Order.objects.get(number=params[3])))
    workOrder.status = WorkOrderStatus.objects.get(key=3)
    workOrder.endTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    workOrder.save()
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
    if params['model'] == 'order':
        selectList = {'orderType': list(
            map(lambda obj: obj.name, OrderType.objects.all())), 'route': list(
            map(lambda obj: obj.name, ProcessRoute.objects.all()))}
    if params['model'] == 'store':
        selectList = {'storeType': list(
            map(lambda obj: obj.name, StoreType.objects.all())), 'workShop': list(
            map(lambda obj: obj.name, WorkShop.objects.all()))}
    if params['model'] == 'productLine':
        selectList = {'state': list(
            map(lambda obj: obj.name, LineState.objects.all())), 'workShop': list(
            map(lambda obj: obj.name, WorkShop.objects.all()))}
    if params['model'] == 'device':
        selectList = {'deviceType': list(
            map(lambda obj: obj.name, DeviceType.objects.all())), 'process': list(
            map(lambda obj: obj.name, Process.objects.all()))}
    if params['model'] == 'productStandard':
        selectList = {'product': list(
            map(lambda obj: obj.name, Product.objects.filter(Q(prodType__key=1)))), 'result': ['合格', '不合格']}
    if params['model'] == 'material':
        selectList = {'group': list(
            map(lambda obj: obj.name, MaterialGroup.objects.all())), 'store': list(
            map(lambda obj: obj.name, Store.objects.all())), 'mateType': ['自制', '外采']}
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
            for i in range(int(description.split(',')[-1].split(':')[1])):
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
                product.name = '%s/%s' % (workOrder.description.split(',')[
                    0].split(':')[1], workOrder.number)
                product.number = str(time.time()*1000000)
                product.workOrder = workOrder
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
    qualData = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Product.objects.filter(Q(prodType__name='合格'))
            .values('batch')
            .annotate(count=Count('batch'))
            .values('batch', 'count')
            )
    )
    unqualData = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Product.objects.filter(Q(prodType__name='不合格'))
            .values('batch')
            .annotate(count=Count('batch'))
            .values('batch', 'count'))
    )
    qualDataRate = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))*1000+8*60*60*1000,
                         round(obj['count']/len(Product.objects.filter(Q(batch__gte=datetime.datetime.now().date()))), 2)],
            Product.objects.filter(Q(prodType__name='合格'))
            .values('batch')
            .annotate(count=Count('batch')).values('batch', 'count'))
    )
    unqualDataRate = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))*1000+8*60*60*1000,
                         round(obj['count']/len(Product.objects.filter(Q(batch__gte=datetime.datetime.now().date()))), 2)],
            Product.objects.filter(Q(prodType__name='不合格'))
            .values('batch')
            .annotate(count=Count('batch'))
            .values('batch', 'count'))
    )
    reasonData = list(
        map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
            Product.objects.filter(Q(prodType__name='不合格'))
            .values('reason')
            .annotate(count=Count('reason'))
            .values('reason', 'count'))
    )
    data = [
        {'name': '合格', 'type': 'column', 'yAxis': 0, 'data': qualData},
        {'name': '合格率', 'type': 'spline', 'yAxis': 1, 'data': qualDataRate},
        {'name': '不合格', 'type': 'column', 'yAxis': 0, 'data': unqualData},
        {'name': '不合格率', 'type': 'spline', 'yAxis': 1, 'data': unqualDataRate},
        {'name': '总计', 'type': 'pie', 'data': reasonData,
            'center': [150, 50], 'size':150}
    ]

    return JsonResponse({'res': data})


@csrf_exempt
def queryExcelData(request):
    data = list(map(lambda obj: {'key': obj.key, 'line': obj.line.name, 'number': obj.number, 'time': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), 'user': obj.creator, 'expectYields': len(WorkOrder.objects.filter(Q(order=obj))), 'realYields': len(
        WorkOrder.objects.filter(Q(status__name='已完成', order=obj))), 'rate': round(len(Product.objects.filter(Q(prodType__name='合格', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))), 2)}, Order.objects.all()))
    return JsonResponse({'res': data})


@csrf_exempt
def exportData(request):
    excelData = list(map(lambda obj: {'key': obj.key, 'line': obj.line.name, 'number': obj.number, 'time': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), 'user': obj.creator, 'expectYields': len(WorkOrder.objects.filter(Q(order=obj))), 'realYields': len(
        WorkOrder.objects.filter(Q(status__name='已完成', order=obj))),  'rate': round(len(Product.objects.filter(Q(prodType__name='合格', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))), 2)}, Order.objects.all()))

    excel = []
    for data in excelData:
        excel.append({'订单编号': data['number'], '下单日期': data['time'], '下单客户': data['user'],
                      '产线名称': data['line'], '预期产量': data['expectYields'], '实际产量': data['realYields'], '合格率': data['rate']})
    df = pd.DataFrame(excel)
    df.to_excel(BASE_DIR+'/upload/export/产能报表.xlsx')

    return JsonResponse({'res': 'http://192.168.1.103:8899/upload/export/产能报表.xlsx'})
