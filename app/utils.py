import datetime
from app.models import *
from django.db.models import Q
from django.db.models.aggregates import Count, Sum


def powerAna():
    data = [
        {'name': '预期产量', 'type': 'column',
            'data': list(map(lambda obj:  len(
                WorkOrder.objects.filter(Q(order=obj))), Order.objects.all()))},
        {'name': '实际产量', 'type': 'column', 'data':  list(map(lambda obj:   len(
            WorkOrder.objects.filter(Q(status__name='已完成', order=obj))), Order.objects.all()))},
        {'name': '合格率', 'type': 'column', 'data': list(map(lambda obj: round(len(Product.objects.filter(
            Q(result='1', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))) if len(WorkOrder.objects.filter(Q(order=obj))) != 0 else 1, 2), Order.objects.all()))},
    ]
    return data


def qualAna():
    data = Product.objects.all().values('batch').annotate(good=Count('result', filter=Q(
        result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
    goodData = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                         * 1000+8*60*60*1000, obj['good']], data))
    badData = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                         * 1000+8*60*60*1000, obj['bad']], data))
    goodRate = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                         * 1000+8*60*60*1000, round(obj['good']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) !=0 else 1, 2)], data))
    badRate = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                         * 1000+8*60*60*1000, round(obj['bad']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) !=0 else 1, 2)], data))

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
        {'name': '不合格率', 'type': 'spline', 'yAxis': 1, 'data': badRate},
        {'name': '总计', 'type': 'pie', 'data': reasonData,
            'center': [150, 50], 'size':150}
    ]
    return data


def mateAna():
    markerRed = {
        'fillColor': {
            'radialGradient': {'cx': 0.4, 'cy': 0.3, 'r': 0.7},
            'stops': [
                [0, 'rgba(255,255,255,0.5)'],
                [1, 'rgba(255,0,0,0.5)']
            ]
        }
    }
    markerGreen = {
        'fillColor': {
            'radialGradient': {'cx': 0.4, 'cy': 0.3, 'r': 0.7},
            'stops': [
                [0, 'rgba(255,255,255,0.5)'],
                [1, 'rgba(0,255,0,0.5)']
            ]
        }
    }
    markerBlue = {
        'fillColor': {
            'radialGradient': {'cx': 0.4, 'cy': 0.3, 'r': 0.7},
            'stops': [
                [0, 'rgba(255,255,255,0.5)'],
                [1, 'rgba(0,0,255,0.5)']
            ]
        }
    }
    redBottle = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Bottle.objects.filter(Q(color='红瓶')).values('createTime').annotate(
            count=Count('createTime')).values('createTime', 'count')
            ))
    greenBottle = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Bottle.objects.filter(Q(color='绿瓶')).values('createTime').annotate(
            count=Count('createTime')).values('createTime', 'count')
            ))
    blueBottle = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Bottle.objects.filter(Q(color='蓝瓶')).values('createTime').annotate(
            count=Count('createTime')).values('createTime', 'count')
            ))
    cup = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['count']],
            Bottle.objects.all().values('createTime').annotate(
            count=Count('createTime')).values('createTime', 'count')
            ))
    red = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['reds'], 1],
            Bottle.objects.all().values('createTime', 'order', 'red').annotate(
                reds=Sum('red')).values('createTime', 'reds').annotate(count=Count('red')).values('createTime', 'reds')
            ))
    green = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['greens'], 1],
            Bottle.objects.all().values('createTime', 'order', 'green').annotate(
                greens=Sum('green')).values('createTime', 'greens').annotate(count=Count('green')).values('createTime', 'greens')
            ))
    blue = list(
        map(lambda obj: [int(time.mktime(obj['createTime'].timetuple()))*1000+8*60*60*1000, obj['blues'], 1],
            Bottle.objects.all().values('createTime', 'order', 'blue').annotate(
                blues=Sum('blue')).values('createTime', 'blues').annotate(count=Count('blue')).values('createTime', 'blues')
            ))

    data = [
        {'name': '瓶盖', 'type': 'spline', 'color': 'gold', 'data': cup},
        {'name': '红瓶', 'type': 'column', 'color': 'red', 'data': redBottle},
        {'name': '绿瓶', 'type': 'column', 'color': 'green', 'data': greenBottle},
        {'name': '蓝瓶', 'type': 'column', 'color': 'blue', 'data': blueBottle},
        {'name': '红粒', 'type': 'bubble', 'yAxis': 1,
            'color': 'red', 'marker': markerRed, 'data': red},
        {'name': '绿粒', 'type': 'bubble', 'yAxis': 1,
            'color': 'green', 'marker': markerGreen, 'data': green},
        {'name': '蓝粒', 'type': 'bubble', 'yAxis': 1,
            'color': 'green', 'marker': markerBlue, 'data': blue},
    ]
    return data


def storeAna():
    data = [
        {'name': '库存统计', 'type': 'column', 'data': list(map(lambda obj: [obj['name'], obj['counts']], Material.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'counts')))}
    ]
    return data


def selectPosition(product):
    res = ''
    if product.pallet:
        if product.pallet.hole1Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '1')
        elif product.pallet.hole2Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '2')
        elif product.pallet.hole3Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '3')
        elif product.pallet.hole4Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '4')
        elif product.pallet.hole5Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '5')
        elif product.pallet.hole6Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '6')
        elif product.pallet.hole7Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '7')
        elif product.pallet.hole8Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '8')
        elif product.pallet.hole9Content == product.workOrder.bottle:
            res = '%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '9')
        else:
            pass
    return res
