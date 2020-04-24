import datetime
from app.models import *
from django.db.models import Q
from django.db.models.aggregates import Count, Sum


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

    data = [
        {'name': '预期产量', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': expectData[-20:]},
        {'name': '实际产量', 'type': 'column',
            'color': 'rgb(255,77,79)', 'data': realData[-20:]},
        {'name': '合格率', 'type': 'line', 'yAxis': 1, 'data': goodRate[-20:]},
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
             }, 'data': expectData[-20:]},
            {'name': '实际产量', 'type': 'column',
             'color': {
                 'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                 'stops': [
                     [0, 'rgba(255,77,79,0)'],
                     [1, 'rgba(255,77,79,1)']
                 ]
             }, 'data': realData[-20:]},
        ]
    return data


def qualAna(orderType, all):
    data = Product.objects.filter(Q(workOrder__order__orderType__name=orderType)).values('batch').annotate(good=Count(
        'result', filter=Q(result='1')), bad=Count('result', filter=Q(result='2'))).values('batch', 'good', 'bad')
    goodData = list(
        map(lambda obj: [dataX(obj['batch']), obj['good']], data))
    badData = list(
        map(lambda obj: [dataX(obj['batch']), obj['bad']], data))
    goodRate = list(map(lambda obj: [dataX(obj['batch']), rateY(obj)], data))
    reasonData = list(
        map(lambda obj: {'name': obj['reason'], 'y': obj['count']},
            Product.objects.filter(
                Q(result='2', workOrder__order__orderType__name='灌装'))
            .values('reason')
            .annotate(count=Count('reason'))
            .values('reason', 'count'))
    )
    data = [
        {'name': '合格', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': goodData[-20:]},
        {'name': '不合格', 'type': 'column',
            'color': 'rgb(255,77,79)', 'data': badData[-20:]},
        {'name': '原因汇总', 'type': 'pie', 'data': reasonData, 'innerSize': '50%',
            'center': [150, 80], 'size':200}
    ]
    if all or orderType == '机加':
        data = [
            {'name': '合格', 'type': 'column',
                'color': {
                    'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                    'stops': [
                     [0, 'rgba(24,144,255,0)'],
                     [1, 'rgba(24,144,255,1)']
                    ]
                }, 'data': goodData[-20:]},
            {'name': '不合格', 'type': 'column',
                'color': {
                    'linearGradient': {'x1': 0, 'x2': 0, 'y1': 1, 'y2': 0},
                    'stops': [
                     [0, 'rgba(255,77,79,0)'],
                     [1, 'rgba(255,77,79,1)']
                    ]
                }, 'data': badData[-20:]},
        ]

    return data


def mateAna():
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
            'color': 'rgb(24,144,255)', 'data': red[-20:]},
        {'name': '红瓶', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': redBottle[-20:]},
        {'name': '绿粒', 'type': 'column',
            'color': 'rgb(24,144,255)',  'data': green[-20:]},
        {'name': '绿瓶', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': greenBottle[-20:]},
        {'name': '蓝粒', 'type': 'column',
            'color': 'rgb(24,144,255)',  'data': blue[-20:]},
        {'name': '蓝瓶', 'type': 'column',
            'color': 'rgb(24,144,255)', 'data': blueBottle[-20:]},
        {'name': '瓶盖', 'type': 'areaspline',
            'color': 'rgb(24,144,255)', 'data': cap[-20:]},
    ]
    return data


def storeAna():
    data = [
        {'name': '库存统计', 'type': 'pie', 'innerSize': '80%', 'name': '库存剩余', 'data': list(map(lambda obj: {'name': obj['name'], 'y':obj['counts']}, Material.objects.all().values('name').annotate(
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
