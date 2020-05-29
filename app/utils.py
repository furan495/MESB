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


def updateDevice(device):
    device.process = None
    device.save()


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


def formatSql(sqlList):
    sqlList.insert(
        1, 'ROW_NUMBER() OVER(ORDER BY [app_order].[number]) AS 编号,')
    for sql in sqlList:
        if u'\u4e00' <= sql <= u'\u9fff' or ('[' not in sql and re.compile(u'[\u4e00-\u9fa5]').search(sql)):
            sqlList[sqlList.index(sql)] = '\'%s\'' % sql
    return ' '.join(sqlList)


def selectStatus(storeType, index, count):
    if '灌装' == storeType:
        return '1'
    if '机加' == storeType:
        return '4'
    if '电子装配' == storeType:
        return '4'


def selectDescription(storeType, index, count, row, col):
    if '机加' == storeType:
        if index < int(count/2):
            return '原料'
        else:
            return '成品'
    if '电子装配' == storeType:
        if ProductType.objects.filter(Q(orderType__name='电子装配')).count() > 0:
            products = ProductType.objects.filter(
                Q(orderType__name='电子装配')).values_list('name')
            if index < int(count/2):
                for i in range(len(products)):
                    if int(i*col/2) <= index < int(i*col/2)+4:
                        return '%s原料' % products[i][0]
            else:
                for i in range(len(products)):
                    if (row+i)*col/2 <= index < (row+i)*col/2+4:
                        return '%s成品' % products[i][0]
        else:
            return '待定仓位'
    else:
        return '分组'


def positionSelect(obj, position):
    try:
        return Event.objects.get(workOrder=obj, source=position).time.strftime(
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
    return Operate.objects.filter(Q(name='登陆系统', time__gte=start, time__lte=stop)).count()


def rateY(obj):
    return round(obj['good']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) != 0 else 0, 2)


def powerAna(orderType, all):
    data = Product.objects.filter(Q(workOrder__order__orderType__name=orderType)).values('batch').annotate(reals=Count('batch', filter=Q(workOrder__status__name='已完成')), expects=Count(
        'batch'), good=Count('result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad', 'expects', 'reals')
    expectData = list(
        map(lambda obj: [dataX(obj['batch']), obj['expects']], data))
    realData = list(map(lambda obj: [dataX(obj['batch']), obj['reals']], data))
    goodRate = list(map(lambda obj: [dataX(obj['batch']), rateY(obj)], data))

    if data.count() == 0:
        expectData, realData, goodRate = [], [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        start = '%s-%s-20' % (str(year), str(month-1))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000, time.time()*1000, 24*60*60*1000):
            expectData.append([day, random.randint(1, 100)])
            realData.append([day, random.randint(1, 100)])
            goodRate.append([day, round(random.random(), 2)])

    data = [
        {'name': '预期产量', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': expectData},
        {'name': '实际产量', 'type': 'column',
            'color': 'rgb(255,77,79)', 'data': realData},
        {'name': '合格率', 'type': 'line', 'color': '#40a9ff',
            'yAxis': 1, 'data': goodRate},
    ]
    if all:
        data = [
            {'name': '预期产量', 'type': 'column',
             'color': {
                 'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                 'stops': [
                     [0, 'rgba(24,144,255,0)'],
                     [1, 'rgba(24,144,255,1)']
                 ]
             }, 'data': expectData},
            {'name': '实际产量', 'type': 'column',
             'color': {
                 'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                 'stops': [
                     [0, 'rgba(255,77,79,0)'],
                     [1, 'rgba(255,77,79,1)']
                 ]
             }, 'data': realData},
        ]
    return data


def qualAna(orderType, all):
    data = Product.objects.filter(Q(workOrder__order__orderType__name=orderType)).values('batch').annotate(good=Count(
        'result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
    goodData = list(
        map(lambda obj: [dataX(obj['batch']), obj['good']], data))
    badData = list(
        map(lambda obj: [dataX(obj['batch']), obj['bad']], data))
    reasonData = list(
        map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
            Product.objects.filter(
                Q(result='2', workOrder__order__orderType__name=orderType))
            .values('reason')
            .annotate(count=Count('reason'))
            .values('reason', 'count'))
    )

    if data.count() == 0:
        goodData, badData, reasonData = [], [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        start = '%s-%s-20' % (str(year), str(month-1))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000, time.time()*1000, 24*60*60*1000):
            goodData.append([day, random.randint(1, 100)])
            badData.append([day, random.randint(1, 100)])
        for reason in ['原因1', '原因2', '原因3', '原因4', '原因5']:
            reasonData.append({'name': reason, 'y': random.randint(20, 100)})

    data = [
        {'name': '合格', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': goodData},
        {'name': '不合格', 'type': 'column',
            'color': 'rgb(255,77,79)', 'data': badData},
        {'name': '原因汇总', 'type': 'pie', 'data': reasonData, 'innerSize': '50%',
            'center': [150, 80], 'size':200}
    ]
    if all:
        data = [
            {'name': '合格', 'type': 'column',
                'color': {
                    'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                    'stops': [
                     [0, 'rgba(24,144,255,0)'],
                     [1, 'rgba(24,144,255,1)']
                    ]
                }, 'data': goodData},
            {'name': '不合格', 'type': 'column',
                'color': {
                    'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                    'stops': [
                     [0, 'rgba(255,77,79,0)'],
                     [1, 'rgba(255,77,79,1)']
                    ]
                }, 'data': badData},
        ]

    return data


def mateAna(orderType, all):
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
            {'name': '红粒', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': red},
            {'name': '红瓶', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': redBottle},
            {'name': '绿粒', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': green},
            {'name': '绿瓶', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': greenBottle},
            {'name': '蓝粒', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': blue},
            {'name': '蓝瓶', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': blueBottle},
        ]
    if orderType == '机加':
        data = Product.objects.filter(Q(workOrder__order__orderType__name=orderType)).values('batch').annotate(
            count=Count('batch', filter=Q(workOrder__status__name='已完成'))).values('batch', 'count')
        day = list(map(lambda obj: [dataX(obj['batch']), obj['count']], data))
        data = [
            {'name': '原料棒', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': day},
        ]
    if orderType == '电子装配':
        materialDict = {}
        materials = Material.objects.filter(
            Q(store__storeType__name='原料库', store__productLine__lineType__name='电子装配')).values('name', 'size').distinct()
        for material in materials:
            materialDict[material['name']] = Sum('prodType__bom__contents__counts', filter=Q(
                prodType__bom__contents__material=material['name']+'/'+material['size']))

        results = Product.objects.filter(Q(workOrder__order__orderType__name=orderType)).values(
            'batch').annotate(**materialDict).values('batch', *materialDict.keys())

        for mate in materials:
            data.append({'name': mate['name'], 'type': 'column', 'color': 'rgb(24,144,255)', 'data': list(
                map(lambda obj: [dataX(obj['batch']), obj[mate['name']]], results))
            })

    if len(data) == 0:
        one, two, three, four, five, six, seven, eight, nine, ten = [
        ], [], [], [], [], [], [], [], [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        start = '%s-%s-20' % (str(year), str(month-1))
        for day in np.arange(int(time.mktime(time.strptime(start, '%Y-%m-%d')))*1000, time.time()*1000, 24*60*60*1000):
            one.append([day, random.randint(1, 100)])
            two.append([day, random.randint(1, 100)])
            three.append([day, random.randint(1, 100)])
            four.append([day, random.randint(1, 100)])
            five.append([day, random.randint(1, 100)])
            six.append([day, random.randint(1, 100)])
            seven.append([day, random.randint(1, 100)])
            eight.append([day, random.randint(1, 100)])
            nine.append([day, random.randint(1, 100)])
            ten.append([day, random.randint(1, 100)])
        data = [
            {'name': '物料1', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': one},
            {'name': '物料2', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': two},
            {'name': '物料3', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': three},
            {'name': '物料4', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': four},
            {'name': '物料5', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': five},
            {'name': '物料6', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': six},
            {'name': '物料7', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': seven},
            {'name': '物料8', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': eight},
            {'name': '物料9', 'type': 'column',
                'color': 'rgb(24,144,255)',  'data': nine},
            {'name': '物料10', 'type': 'column',
                'color': 'rgb(24,144,255)', 'data': ten},
        ]
    return data


def storeAna(order):
    data = [
        {'name': '库存统计', 'type': 'pie', 'innerSize': '80%', 'name': '库存剩余', 'data': list(map(lambda obj: {'name': obj['name'], 'y':obj['counts']}, Material.objects.filter(Q(store__productLine__lineType__name=order)).values('name').annotate(
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
            pos = StorePosition.objects.get(
                content='%s-%s' % (product.name, product.workOrder.number))
            res = '%s-%s号位' % (pos.store.name, pos.number.split('-')[0])
        except Exception as e:
            res = ''
    return res
