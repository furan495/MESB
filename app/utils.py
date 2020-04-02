import datetime
from app.models import *
from django.db.models import Q
from django.db.models.aggregates import Count, Sum


def positionSelect(obj, position):
    try:
        return Event.objects.get(workOrder=obj, source=position).time.strftime(
            '%Y-%m-%d %H:%M:%S')
    except:
        return ''


def powerAna():
    data = [
        {'name': '预期产量', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#00C1FF00'],
                [1, '#00C1FFFF']
            ]
        }, 'data': list(map(lambda obj:  len(
            WorkOrder.objects.filter(Q(order=obj))), Order.objects.all()))[-20:]},
        {'name': '实际产量', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#22E1B400'],
                [1, '#22E1B4FF']
            ]
        }, 'data':  list(map(lambda obj:   len(
            WorkOrder.objects.filter(Q(status__name='已完成', order=obj))), Order.objects.all()))[-20:]},
        {'name': '合格率', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#762EFF00'],
                [1, '#762EFFFF']
            ]
        }, 'data': list(map(lambda obj: round(len(Product.objects.filter(
            Q(result='1', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))) if len(WorkOrder.objects.filter(Q(order=obj))) != 0 else 1, 2), Order.objects.all()))[-20:]},
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
                         * 1000+8*60*60*1000, round(obj['good']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) != 0 else 1, 2)], data))
    badRate = list(
        map(lambda obj: [int(time.mktime(obj['batch'].timetuple()))
                         * 1000+8*60*60*1000, round(obj['bad']/(obj['good']+obj['bad']) if (obj['good']+obj['bad']) != 0 else 1, 2)], data))
    reasonData = list(
        map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
            Product.objects.filter(Q(result='2'))
            .values('reason')
            .annotate(count=Count('reason'))
            .values('reason', 'count'))
    )
    data = [
        {'name': '合格', 'type': 'column', 'color': '#00C1FF',
            'yAxis': 0, 'data': goodData[-20:]},
        {'name': '合格率', 'type': 'spline', 'dashStyle': 'Dot',
            'color': '#E65608', 'yAxis': 1, 'data': goodRate[-20:]},
        {'name': '不合格', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#762EFF00'],
                [1, '#762EFFFF']
            ]
        }, 'yAxis': 0, 'data': badData[-20:]},
        {'name': '不合格率', 'type': 'spline', 'dashStyle': 'Dot',
            'color': '#762EFF', 'yAxis': 1, 'data': badRate[-20:]},
        {'name': '总计', 'type': 'pie', 'color': '#00C1FF', 'data': reasonData,
            'center': [150, 50], 'size':150}
    ]
    return data


def mateAna():
    markerRed = {
        'fillColor': {
            'radialGradient': {'cx': 0.5, 'cy': 0.5, 'r': 3},
            'stops': [
                [0, '#F2005F00'],
                [1, '#F2005FFF']
            ]
        }
    }
    markerGreen = {
        'fillColor': {
            'radialGradient': {'cx': 0.5, 'cy': 0.5, 'r': 3},
            'stops': [
                [0, '#00FFBF00'],
                [1, '#00FFBFFF']
            ]
        }
    }
    markerBlue = {
        'fillColor': {
            'radialGradient': {'cx': 0.5, 'cy': 0.5, 'r': 3},
            'stops': [
                [0, '#0087FE00'],
                [1, '#0087FEFF']
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
        {'name': '瓶盖', 'type': 'spline', 'dashStyle': 'Dot',
            'color': 'gold', 'data': cup},
        {'name': '红瓶', 'type': 'column',
            'color': '#F2005F', 'data': redBottle[-20:]},
        {'name': '绿瓶', 'type': 'column',
            'color': '#00FFBF', 'data': greenBottle[-20:]},
        {'name': '蓝瓶', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#0087FE00'],
                [1, '#0087FEFF']
            ]
        }, 'data': blueBottle[-20:]},
        {'name': '红粒', 'type': 'bubble', 'yAxis': 1,
            'color': '#F2005F', 'marker': markerRed, 'data': red[-20:]},
        {'name': '绿粒', 'type': 'bubble', 'yAxis': 1,
            'color': '#00FFBF', 'marker': markerGreen, 'data': green[-20:]},
        {'name': '蓝粒', 'type': 'bubble', 'yAxis': 1,
            'color': '#0087FE', 'marker': markerBlue, 'data': blue[-20:]},
    ]
    return data


def storeAna():
    data = [
        {'name': '库存统计', 'type': 'column', 'color': {
            'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
            'stops': [
                [0, '#762EFF00'],
                [1, '#762EFFFF']
            ]
        }, 'data': list(map(lambda obj: [obj['name'], obj['counts']], Material.objects.all().values('name').annotate(
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
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '2')
        elif product.pallet.hole3Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '3')
        elif product.pallet.hole4Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '4')
        elif product.pallet.hole5Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '5')
        elif product.pallet.hole6Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '6')
        elif product.pallet.hole7Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '7')
        elif product.pallet.hole8Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '8')
        elif product.pallet.hole9Content == product.workOrder.bottle:
            res='%s-%s号位-%s号孔' % (product.pallet.position.store.name,
                                    product.pallet.position.number.split('-')[0], '9')
        else:
            pass
    return res
