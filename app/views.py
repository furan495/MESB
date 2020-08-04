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
def wincc(request):
    """ params = json.loads(str(request.body, 'utf8').replace('\'', '\"'))[
        'str'].split(',') """

    params = str(request.body, 'utf8').split(',')

    workOrder = WorkOrder.objects.get(Q(number=params[1]))
    product = workOrder.product
    standard = ProductStandard.objects.get(Q(product=product))

    if 'start' in params[0]:
        if params[0].split('-')[1] == 'LP':
            product.number = params[2]
            product.save()
        workOrder.startTime = datetime.datetime.now()
        workOrder.status = CommonStatus.objects.get(name='加工中')
    if 'stop' in params[0]:
        if params[0].split('-')[1] == 'D':
            product.status = CommonStatus.objects.get(name='半成品')
            product.save()
        workOrder.endTime = datetime.datetime.now()
        workOrder.status = CommonStatus.objects.get(name='已完成')

    if params[0] == 'stop-%s' % Process.objects.filter(Q(route=WorkOrder.objects.get(number=params[1]).product.order.route)).last().number:
        product.status = CommonStatus.objects.get(name='已完成')
        product.save()
        order = product.order
        if order.products.all().filter(Q(status=None)).count() == 0:
            order.status = CommonStatus.objects.get(name='已完成')
            order.save()
    workOrder.save()

    if params[0] == 'check':
        if random.random() > 0.5:
            product.result = '合格'
            standard.result = '合格'
            standard.realValue = '合格'
        else:
            product.result = '不合格'
            standard.result = '不合格'
            standard.realValue = '不合格'
        product.save()
        standard.save()

    if params[0] == 'weight':
        standard.realValue = float(params[2])
        if np.abs(standard.realValue-float(standard.expectValue)) <= product.prodType.errorRange:
            standard.result = '合格'
            product.result = '合格'
        else:
            standard.result = '不合格'
            product.result = '不合格'
        standard.save()
        product.save()

    try:
        event = Event()
        event.workOrder = workOrder
        event.source = Process.objects.get(number=params[0].split(
            '-')[1], route=WorkOrder.objects.get(number=params[1]).product.order.route).name
        event.title = '%s%s' % (Process.objects.get(
            number=params[0].split('-')[1], route=WorkOrder.objects.get(number=params[1]).product.order.route).name, '开始' if params[0].split('-')[0] == 'start' else '结束')
        event.save()
    except Exception as e:
        print(e)

    return JsonResponse({'ok': 'ok'})


@csrf_exempt
def selects(request):
    """ for pos in StorePosition.objects.filter(Q(store__storeType__name='原料库')):
        pos.status = '1'
        pos.save() 

    for pos in StorePosition.objects.filter(Q(store__storeType__name='成品库')):
        pos.status = '2'
        pos.save() """

    params = json.loads(request.body)
    selectList = {}
    if params['model'] == 'order' or params['model'] == 'productType':
        selectList = {
            'line': list(map(lambda obj: obj.name, ProductLine.objects.all())),
            'customer': list(map(lambda obj: obj.name, Customer.objects.all())),
            'orderType': list(map(lambda obj: obj.name, OrderType.objects.all())),
            'route': list(map(lambda obj: obj.name, ProcessRoute.objects.filter(~Q(processes__key=None)))),
            'product': list(map(lambda obj: [obj.name, obj.orderType.name], ProductType.objects.filter(~Q(bom__contents__key=None)))),
            'materials': list(map(lambda obj: {'name': obj['name'], 'size': obj['size']}, Material.objects.all().values('name', 'size').distinct()))
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
            'deviceType': list(map(lambda obj: obj.name, DeviceType.objects.all())),
        }
    if params['model'] == 'document':
        selectList = {
            'docType': list(map(lambda obj: [obj.name, obj.key], DocType.objects.all()))
        }
    if params['model'] == 'material' or params['model'] == 'tool':
        selectList = {
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
def queryCharts(request):
    params = json.loads(request.body)
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
    stop = datetime.datetime.strptime(
        params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
    data = Product.objects.filter(Q(order__orderType__name=params['order'])).values('batch').annotate(reals=Count('batch', filter=Q(
        workOrders__status__name='已完成')), expects=Count('batch'), good=Count('result', filter=Q(result='合格')), bad=Count('result', filter=Q(result='不合格')))

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

    progress = list(map(lambda obj: {'key': obj.key, 'number': obj.number[-4:], 'progress': round(obj.workOrders.all().filter(Q(status__name='已完成')).count(
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
