import re
import time
import random
import datetime
import numpy as np
from app.models import *
from django.db.models import Q, F
from django.db.models.aggregates import Count, Sum


def addkey(obj, objs):
    obj['key'] = objs.index(obj)+1
    return obj


def containerChinese(chars):
    for char in chars:
        if '\u4e00' <= char <= '\u9fa5':
            return True
    return False


def width(model, field):
    if model == 'role' and field.name != 'authority':
        return '10%'
    if model == 'bom' and field.name != 'content':
        return '10%'
    if (model == 'workShop' or model == 'productLine' or model == 'processRoute') and field.name != 'description':
        return '10%'


def loopOrganization(organization):
    def renderChildren(name):
        if Organization.objects.filter(Q(parent=name)).count() != 0:
            return loopOrganization(name)
        else:
            return list(map(lambda obj: {'key': name+'-'+str(obj.key), 'title': obj.name, }, User.objects.filter(Q(department__name=name))))
    data = list(map(lambda obj: {
                'key': obj.key, 'title': obj.name, 'parent': obj.parent, 'children': renderChildren(obj.name)}, Organization.objects.filter(Q(parent=organization))))
    return data


def positionSelect(obj, position):
    try:
        return Event.objects.get(workOrder__product=obj, title=position).time.strftime(
            '%m-%d %H:%M:%S')
    except Exception as e:
        return ''


def dataSource(obj):
    data = {'key': obj.key, 'name': obj.prodType.name}
    for process in Process.objects.all():
        data['start%s' % process.number] = positionSelect(
            obj, '%s开始' % process.name)
        data['stop%s' % process.number] = positionSelect(
            obj, '%s结束' % process.name)
    return data


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
    if Product.objects.all().count() < 20:
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        for i in range(7):
            data.append({'container': 'container%s' % (str(i+1)), 'categories': ['%s-%s' % (str(month if day > 7 else month-1), str(day-i if day > 7 else 30-i))], 'series': [
                {'data': [{'y': random.randint(50, 100), 'target': random.randint(100, 150)}]}]})
    else:
        for category in list(Product.objects.all().values_list('batch', flat=True).distinct()):
            data.append({'container': category, 'categories': [category], 'series': [
                {'data': [{'y': Product.objects.filter(Q(batch=category, status__name='已完成', order__createTime__gte=start, order__createTime__lte=stop)).count(), 'target': Product.objects.filter(Q(batch=category, order__createTime__gte=start, order__createTime__lte=stop)).count()}]}]})

    return data


def qualityChart(orderType, start, stop, all):
    data = Product.objects.filter(Q(order__orderType__name=orderType, order__createTime__gte=start, order__createTime__lte=stop)).values('batch').annotate(good=Count(
        'number', filter=Q(result='合格')), reals=Count('number', filter=Q(status__name='已完成')), bad=Count('number', filter=Q(result='不合格')))
    goodRate = list(map(lambda obj: [dataX(obj['batch']), rateY(obj)], data))

    if data.count() < 10:
        goodData, badData = [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        start = '%s-%s-%s' % (str(year), str(month-1 if day <
                                             14 else month), str(np.abs(day-15)))
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
    def seriesData(name, querySet, material):
        series = []
        for query in querySet.annotate(**material):
            series.append([dataX(query['product__batch']), query[name]])
        return series

    data, material = [], {}
    querySet = ProductInfo.objects.filter(Q(product__order__orderType__name=orderType, product__order__createTime__gte=start,
                                            product__order__createTime__lte=stop)).values('product__batch').distinct()
    for mat in BOMContent.objects.all().values_list('material', flat=True).distinct():
        material[mat.split('/')[0]] = Sum('value', filter=Q(name=mat))

    for name in material.keys():
        data.append({'name': name, 'type': 'column',
                     'data': seriesData(name, querySet, material)})

    if len(querySet) < 10:
        one, two, three = [], [], []
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        start = '%s-%s-%s' % (str(year), str(month-1 if day <
                                             14 else month), str(np.abs(day-15)))
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
        {'type': 'pie', 'innerSize': '60%', 'name': '库存剩余', 'data': list(map(lambda obj: {'name': obj['name'], 'y':obj['counts']}, Material.objects.filter(
            Q(store__productLine__lineType__name=order)).values('name').annotate(counts=Count('size'))))}
    ]
    return data
