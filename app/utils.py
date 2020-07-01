import re
import time
import random
import datetime
import numpy as np
from app.models import *
from django.db.models import Q
from django.db.models.aggregates import Count, Sum


def addkey(obj, objs):
    obj['key'] = objs.index(obj)
    return obj


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


def loopOrganization(organization):
    def renderChildren(name):
        if Organization.objects.filter(Q(parent=name)).count() != 0:
            return loopOrganization(name)
        else:
            return list(map(lambda obj: {'key': obj.key, 'title': obj.name, }, User.objects.filter(Q(department__name=name))))
    data = list(map(lambda obj: {
                'key': obj.key, 'title': obj.name, 'parent': obj.parent, 'children': renderChildren(obj.name)}, Organization.objects.filter(Q(parent=organization))))
    return data


def positionSelect(obj, position):
    try:
        return Event.objects.get(workOrder__product=obj, title=position).time.strftime(
            '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return ''


def dataX(date):
    try:
        return int(time.mktime(date.timetuple())) * 1000+8*60*60*1000
    except:
        return 0


def dataY(date):
    start = date.date()
    stop = date.date()+datetime.timedelta(hours=24)
    return Operate.objects.filter(Q(name='登录系统', time__gte=start, time__lte=stop)).count()


def rateY(obj):
    return round(obj['good']/obj['reals'] if obj['reals'] != 0 else 1, 2)


def powerChart(orderType, start, stop, all):
    data = []
    if Product.objects.all().count() == 0:
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        start = '%s-%s' % (str(month), str(day-7))
        for i in range(7):
            data.append({'container': 'container%s' % (str(i+1)), 'categories': ['%s-%s' % (str(month), str(day-i))], 'series': [
                {'data': [{'y': random.randint(50, 100), 'target': random.randint(100, 150)}]}]})
    else:
        for category in list(Product.objects.all().values_list('batch', flat=True).distinct()):
            data.append({'container': category, 'categories': [category], 'series': [
                {'data': [{'y': Product.objects.filter(Q(batch=category, status__name='入库')).count(), 'target': Product.objects.filter(Q(batch=category)).count()}]}]})

    return data


def qualityChart(orderType, start, stop, all):
    data = Product.objects.filter(Q(order__orderType__name=orderType, order__createTime__gte=start, order__createTime__lte=stop)).values('batch').annotate(good=Count(
        'number', filter=Q(result='合格')), reals=Count('number', filter=Q(status__name='入库')), bad=Count('number', filter=Q(result='不合格'))).values('batch', 'good', 'bad', 'reals')
    goodRate = list(map(lambda obj: [dataX(obj['batch']), rateY(obj)], data))

    if data.count() == 0:
        goodData, badData = [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        start = '%s-%s-%s' % (str(year), str(month-1 if day<14 else month ), str(np.abs(day-14)))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000+8*60*60*1000, time.time()*1000, 24*60*60*1000):
            if all:
                badData.append(random.randint(10, 20))
                goodData.append(random.randint(-20, -10))
            else:
                goodData.append([day, random.randint(10, 20)])
                badData.append([day, random.randint(10, 20)])
                goodRate.append([day, round(random.random(), 2)])
    else:
        if all:
            goodData = list(
                map(lambda obj: -obj['good'], data))
            badData = list(
                map(lambda obj: obj['bad'], data))
        else:
            goodData = list(
                map(lambda obj: [dataX(obj['batch']), obj['good']], data))
            badData = list(
                map(lambda obj: [dataX(obj['batch']), obj['bad']], data))

    data = [
        {'name': '合格', 'type': 'bar' if all else 'column',
         'color': 'rgb(155,183,255)', 'data': goodData[-15:]},
        {'name': '不合格', 'type': 'bar' if all else 'column',
         'color': 'rgb(190,147,255)', 'data': badData[-15:]},
    ]

    if not all:
        data.append({'name': '合格率', 'type': 'line',
                     'yAxis': 1, 'data': goodRate[-15:]})

    return data


def materialChart(orderType, start, stop, all):
    data = []
    if orderType == '灌装':
        redBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='红瓶')).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        greenBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='绿瓶')).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        blueBottle = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.filter(Q(color='蓝瓶')).values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        cap = list(
            map(lambda obj: [dataX(obj['createTime']), obj['count']],
                Bottle.objects.all().values('createTime').annotate(
                count=Count('createTime')).values('createTime', 'count')
                ))
        red = list(
            map(lambda obj: [dataX(obj['createTime']), obj['reds']],
                Bottle.objects.all().values('createTime', 'order', 'red').annotate(
                    reds=Sum('red')).values('createTime', 'reds').annotate(count=Count('red')).values('createTime', 'reds')
                ))
        green = list(
            map(lambda obj: [dataX(obj['createTime']), obj['greens']],
                Bottle.objects.all().values('createTime', 'order', 'green').annotate(
                    greens=Sum('green')).values('createTime', 'greens').annotate(count=Count('green')).values('createTime', 'greens')
                ))
        blue = list(
            map(lambda obj: [dataX(obj['createTime']), obj['blues']],
                Bottle.objects.all().values('createTime', 'order', 'blue').annotate(
                    blues=Sum('blue')).values('createTime', 'blues').annotate(count=Count('blue')).values('createTime', 'blues')
                ))

        data = [
            {'name': '红粒', 'type': 'column', 'data': red},
            {'name': '红瓶', 'type': 'column', 'data': redBottle},
            {'name': '绿粒', 'type': 'column',  'data': green},
            {'name': '绿瓶', 'type': 'column', 'data': greenBottle},
            {'name': '蓝粒', 'type': 'column', 'data': blue},
            {'name': '蓝瓶', 'type': 'column', 'data': blueBottle},
        ]
    if orderType == '电子装配':
        materialDict = {}
        materials = Material.objects.filter(
            Q(store__storeType__name='原料库', store__productLine__lineType__name='电子装配')).values('name', 'size').distinct()
        for material in materials:
            materialDict[material['name']] = Sum('prodType__bom__contents__counts', filter=Q(
                prodType__bom__contents__material=material['name']+'/'+material['size']))

        results = Product.objects.filter(Q(workOrder__order__orderType__name=orderType, workOrder__order__createTime__gte=start, workOrder__order__createTime__lte=stop)).values(
            'batch').annotate(**materialDict).values('batch', *materialDict.keys())

        for mate in materials:
            data.append({'name': mate['name'], 'type': 'column', 'data': list(
                map(lambda obj: [dataX(obj['batch']), obj[mate['name']]], results))
            })

    products = Product.objects.filter(Q(order__orderType__name=orderType,order__createTime__gte=start,order__createTime__lte=stop)).values('batch').annotate(
        count=Count('batch', filter=Q(workOrders__status__name='已完成'))).values('batch', 'count')

    for batch in list(Product.objects.all().values_list('batch', flat=True).distinct()):
        for bom in BOMContent.objects.all():
            data.append({'name': bom.material.split('/')[0], 'type': 'line', 'data': list(
                map(lambda obj: [dataX(obj['batch']), bom.counts*obj['count']], products))})

    if len(data) == 0:
        one, two, three = [], [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        start = '%s-%s-%s' % (str(year), str(month), str(day-14))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000+8*60*60*1000, time.time()*1000, 24*60*60*1000):
            one.append([day, random.randint(1, 100)])
            two.append([day, random.randint(1, 100)])
            three.append([day, random.randint(1, 100)])
        data = [
            {'name': '物料1', 'type': 'column', 'data': one},
            {'name': '物料2', 'type': 'column', 'data': two},
            {'name': '物料3', 'type': 'column',  'data': three},
        ]

    return data


def storeAna(order):
    data = [
        {'type': 'pie', 'innerSize': '60%', 'name': '库存剩余', 'data': list(map(lambda obj: {'name': obj['name'], 'y':obj['counts']}, Material.objects.filter(Q(store__productLine__lineType__name=order)).values('name').annotate(
            counts=Count('size')).values('name', 'counts')))}
    ]
    return data


def selectPosition(product):
    res = ''
    if product.pallet:
        if product.pallet.hole1Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '1')
        if product.pallet.hole2Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '2')
        if product.pallet.hole3Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '3')
        if product.pallet.hole4Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '4')
        if product.pallet.hole5Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '5')
        if product.pallet.hole6Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '6')
        if product.pallet.hole7Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '7')
        if product.pallet.hole8Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '8')
        if product.pallet.hole9Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '9')
    else:
        try:
            pos = StorePosition.objects.filter(Q(content=product.number)).last()
            res = '%s-%s号位' % (pos.store.name, pos.number.split('-')[0])
        except Exception as e:
            res = ''
    return res
