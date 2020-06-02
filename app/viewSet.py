import os
import json
import datetime
import pypinyin
import numpy as np
import pandas as pd
from app.utils import *
from app.models import *
from django.apps import apps
from functools import reduce
from itertools import product
from app.serializers import *
from rest_framework import viewsets
from django.db.models.functions import Cast
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import FloatField, Q, F
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Count, Sum, Max, Min, Avg

# Create your views here.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorkShopViewSet(viewsets.ModelViewSet):
    queryset = WorkShop.objects.all().order_by('-createTime')
    serializer_class = WorkShopSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'车间编号': obj.number, '车间名称': obj.name,
                                 '车间描述': obj.descriptions}, WorkShop.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all().order_by('-createTime')
    serializer_class = BOMSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'对应产品': obj.product.name, 'bom名称': obj.name, '创建人': obj.creator, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), 'bom内容': ','.join(
            list(map(lambda obj: obj.material+',数量:'+str(obj.counts) if obj.counts else obj.material+',数量:若干', obj.contents.all())))}, BOM.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.parent:
            Organization.objects.filter(
                Q(key=instance.key) | Q(parent=instance.name)).delete()
        else:
            Organization.objects.all().delete()
        return Response('ok')

    def list(self, request, *args, **kwargs):
        organizations = Organization.objects.filter(Q(parent=None))
        data = map(lambda obj: {'key': obj.key, 'title': obj.name, 'parent': obj.parent,
                                'children': loopOrganization(obj.name)}, organizations)

        orgaSeries = Organization.objects.filter(~Q(parent=None))
        series = map(
            lambda obj: [obj.parent if obj.parent else obj.name, obj.name], orgaSeries)

        parents = map(lambda obj: [obj.key, obj.name],
                      Organization.objects.all())

        return Response({'tree': list(data), 'series': list(series), 'parent': list(parents)})


class ProcessParamsViewSet(viewsets.ModelViewSet):
    queryset = ProcessParams.objects.all()
    serializer_class = ProcessParamsSerializer


class OrderTypeViewSet(viewsets.ModelViewSet):
    queryset = OrderType.objects.all()
    serializer_class = OrderTypeSerializer


class BOMContentViewSet(viewsets.ModelViewSet):
    queryset = BOMContent.objects.all()
    serializer_class = BOMContentSerializer


class OrderStatusViewSet(viewsets.ModelViewSet):
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer


class WorkOrderStatusViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderStatus.objects.all()
    serializer_class = WorkOrderStatusSerializer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('-key')
    serializer_class = RoleSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'角色名': obj.name,
                                 '权限范围': obj.authority}, Role.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-key')
    serializer_class = CustomerSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'客户名称': obj.name, '客户编号': obj.number, '联系电话': obj.phone,
                                 '客户等级': obj.level, '公司': obj.company}, Customer.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['post'], detail=False)
    def login(self, request):
        res = ''
        params = request.data
        user = User.objects.get(phone=params['phone'])
        if user.password == params['password']:
            res = UserSerializer(user).data
        else:
            res = 'err'
        return Response({'res': res, 'count': User.objects.filter(Q(status='2')).count()})

    @action(methods=['post'], detail=False)
    def logout(self, request):
        params = request.data
        user = User.objects.get(Q(phone=params['phone']))
        user.status = '1'
        user.save()
        return Response('ok')

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        params = json.loads(request.body)
        user = User.objects.get(key=pk)
        user.status = params['status']
        user.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'角色': obj.role.name, '姓名': obj.name, '性别': '男' if obj.gender == '1' else '女',
                                 '部门': obj.department.name if obj.department else '', '职位': obj.post, '代号': obj.phone}, User.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-key')
    serializer_class = OrderSerializer

    @action(methods=['post'], detail=True)
    def bottles(self, request, pk=None):
        params = request.data
        order = Order.objects.get(key=pk)
        for count in range(params['counts']):
            bottle = Bottle()
            bottle.number = ''
            bottle.order = order
            bottle.red = params['red']
            bottle.blue = params['blue']
            bottle.green = params['green']
            bottle.color = params['product']
            bottle.save()
        return Response('ok')

    @action(methods=['post'], detail=True)
    def preScheduling(self, request, pk=None):
        res, info = 'ok', ''
        params = request.data
        orderType = params['orderType']
        line = ProductLine.objects.get(name=params['line'])
        route = ProcessRoute.objects.get(name=params['route'])
        if orderType == line.lineType.name and orderType == route.routeType.name:
            if orderType == '灌装':
                particles, fieldDict, bottleCounts = {}, {}, False
                descriptions = params['description'].split(';')[:-1]
                for field in apps.get_model('app', 'Bottle')._meta.fields:
                    fieldDict[field.verbose_name] = field.name
                for desc in descriptions:
                    count = desc.split(',')[-1].split(':')[1]
                    bottle = desc.split(',')[0].split(':')[1]
                    try:
                        occupyBot = Bottle.objects.filter(
                            Q(color=bottle, order__status__name='已排产', order__orderType__name='灌装')).count()
                    except:
                        occupyBot = 0
                    if Material.objects.filter(Q(name=bottle)).count()-occupyBot < int(count):
                        res = 'err'
                        bottleCounts = True
                        info = '%s不足，无法排产' % bottle
                    if not bottleCounts:
                        for particle in desc.split(',')[1:-1]:
                            particleKey = particle.split(':')[0]
                            particles[particleKey] = Sum(
                                'bottles__%s' % fieldDict[particleKey])
                        particleCounts = Order.objects.filter(key=pk).annotate(
                            **particles).values(*particles.keys())
                        for parti in particleCounts[0].keys():
                            try:
                                occupyPar = Order.objects.filter(Q(status__name='已排产', order__orderType__name='灌装')).annotate(counts=Sum(
                                    'bottles__%s' % fieldDict[parti])).values('counts')[0]['counts']
                            except:
                                occupyPar = 0
                            if Material.objects.filter(Q(name=parti)).count()-occupyPar < particleCounts[0][parti]:
                                res = 'err'
                                info = '%s不足，无法排产' % parti
            if orderType == '机加':
                count = 0
                descriptions = params['description']
                for desc in descriptions.split(';')[:-1]:
                    count = count+int(desc.split('x')[1])
                occupy = WorkOrder.objects.filter(
                    Q(order__status__name='已排产', order__orderType__name='机加')).count()
                """ mixinPos = StorePosition.objects.filter(
                    Q(store__productLine__lineType__name='机加', store__storeType__name='混合库', status='3', description='原料')).count()
                ylPos = Material.objects.filter(
                    Q(store__storeType__name='原料库', store__productLine__lineType__name='机加')).count()
                if (mixinPos < count) or (ylPos-occupy < count):
                    res = 'err'
                    info = '原料不足，无法排产' """
                if count > StorePosition.objects.filter(Q(store__storeType__name='成品库', status='4')).count():
                    res = 'err'
                    info = '成品库仓位不足，无法排产'
                else:
                    for store in Store.objects.filter(Q(storeType__name='原料库')):
                        if count > StorePosition.objects.filter(Q(store=store, status='3')).count()-occupy:
                            res = 'err'
                            info = '%s不足，无法排产' % Material.objects.filter(Q(store=store))[
                                0].name
            if orderType == '电子装配':
                eaOutPosition, eaInPosition = {}, {}
                for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                    eaOutPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name)).count()
                    eaInPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name)).count()
                descriptions = params['description']
                materialStr, materialDict, bed = '', {}, False
                for desc in descriptions.split(';')[:-1]:
                    product = desc.split('x')[0]
                    productCount = desc.split('x')[1]
                    bom = BOM.objects.get(Q(product__name=product))
                    matStr = map(lambda obj: obj.material, bom.contents.all())
                    materialStr = materialStr + ','.join(list(matStr))+','
                    if eaOutPosition[product] < int(productCount):
                        bed = True
                        res = 'err'
                        info = '%s原料底座不足，无法排产' % product
                    if eaInPosition[product] < int(productCount):
                        bed = True
                        res = 'err'
                        info = '%s成品仓位不足，无法排产' % product
                if not bed:
                    for material in list(set(materialStr.split(',')))[1:]:
                        materialKey = material.split('/')[0]
                        materialDict[materialKey] = 0
                    # print(materialDict)
                    for desc in descriptions.split(';')[:-1]:
                        count = desc.split('x')[1]
                        product = desc.split('x')[0]
                        bom = BOM.objects.get(Q(product__name=product))
                        for mat in bom.contents.all():
                            counts = mat.counts*int(count)
                            matKey = mat.material.split('/')[0]
                            materialDict[matKey] = materialDict[matKey] + counts
                    for mat in list(set(materialStr.split(',')))[1:]:
                        try:
                            bomContents = BOMContent.objects.filter(
                                Q(bom__product__products__workOrder__order__status__name='已排产', bom__product__products__workOrder__order__orderType__name='电子装配')).values('material').distinct().annotate(counts=Sum('counts', filter=Q(material=mat))).values('counts')
                            occupy = list(filter(lambda obj: obj['counts'] != None, bomContents))[
                                0]['counts']
                        except:
                            occupy = 0
                        if Material.objects.filter(Q(name=mat.split('/')[0], size__icontains=mat.split('/')[1])).count()-occupy < materialDict[mat.split('/')[0]]:
                            res = 'err'
                            info = '%s不足，无法排产' % mat
            else:
                pass
        else:
            res = 'err'
            info = '产线或工艺不符，无法排产'

        return Response({'res': res, 'info': info})

    @action(methods=['post'], detail=True)
    def scheduling(self, request, pk=None):
        params = request.data
        order = Order.objects.get(key=pk)
        orderDesc = params['description'].split(';')
        order.status = OrderStatus.objects.get(name='已排产')
        order.batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order.scheduling = params['scheduling'] if params['scheduling'] != '' else datetime.datetime.now(
        ).strftime('%Y-%m-%d %H:%M:%S')
        order.save()
        if params['orderType'] == '灌装':
            for description in orderDesc:
                if len(description.split(',')) > 1:
                    for i in range(int(description.split(',')[-1].split(':')[1])):
                        workOrder = WorkOrder()
                        workOrder.order = order
                        time.sleep(0.1)
                        workOrder.number = str(time.time()*1000000)[:15]
                        workOrder.status = WorkOrderStatus.objects.get(
                            name='等待中')
                        workOrder.description = ','.join(
                            description.split(',')[:4])
                        workOrder.save()

                        product = Product()
                        product.name = workOrder.description.split(',')[
                            0].split(':')[1]
                        product.number = str(time.time()*1000000)
                        product.workOrder = workOrder
                        product.prodType = ProductType.objects.get(Q(orderType=order.orderType, name__icontains=workOrder.description.split(',')[
                            0].split(':')[1]))
                        product.save()

                        standard = ProductStandard()
                        standard.name = '重量'
                        standard.expectValue = str(np.sum(list(map(lambda obj: int(obj)*5, re.findall(
                            '\d+', description[:description.index('份数')])))))
                        standard.product = product
                        standard.save()
        else:
            for description in orderDesc:
                if len(description.split('x')) > 1:
                    for i in range(int(description.split('x')[1])):
                        workOrder = WorkOrder()
                        workOrder.order = order
                        time.sleep(0.1)
                        workOrder.number = str(time.time()*1000000)[:15]
                        workOrder.status = WorkOrderStatus.objects.get(
                            name='等待中')
                        workOrder.description = description.split('x')[0]
                        workOrder.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def products(self, request):
        params = request.data
        workOrder = WorkOrder.objects.filter(
            Q(order__key=params['key']))
        outPos = list(StorePosition.objects.filter(
            Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='3', description__icontains='原料') | Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='原料库', status='3')))[:workOrder.count()]
        outPosition = list(map(lambda obj: obj.number.split('-')[0], outPos))
        inPos = list(StorePosition.objects.filter(
            Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='4', description__icontains='成品') | Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='成品库', status='4')).order_by('-key'))[:workOrder.count()]
        inPosition = list(map(lambda obj: obj.number.split('-')[0], inPos))

        eaOutPosition, eaInPosition = {}, {}

        """ outPos = {}
        for store in Store.objects.filter(Q(storeType__name='原料库')):
            outPos[store.name] = StorePosition.objects.filter(
                Q(store=store, status='3')).values_list('number', flat=True) """

        for i in range(workOrder.count()):
            if params['orderType'] == '电子装配':
                for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                    eaOutPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name))
                    eaInPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name)).order_by('-key')
            product = Product()
            product.name = workOrder[i].description
            product.number = str(time.time()*1000000)
            product.workOrder = workOrder[i]
            """ product.outPos = outPosition[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0].number.split(
                '-')[0] """
            product.inPos = inPosition[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0].number.split(
                '-')[0]
            product.prodType = ProductType.objects.get(
                Q(orderType__name=params['orderType'], name__icontains=workOrder[i].description.split('x')[0]))
            product.save()

            """ outP = outPos[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0]
            outP.status = '4'
            outP.save()
            inP = inPos[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0]
            inP.status = '3'
            inP.save() """

            standard = ProductStandard()
            standard.name = '外观'
            standard.expectValue = '合格'
            standard.product = product
            standard.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'订单类别': obj.orderType.name, '选用工艺': obj.route.name, '订单状态': obj.status.name, '创建人': obj.creator, '目标客户': obj.customer.name,
                                 '订单编号': obj.number, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), '排产时间': obj.scheduling, '订单批次': obj.batch, '订单描述': obj.description}, Order.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])

    @action(methods=['get'], detail=True)
    def gantt(self, request, pk=None):
        order = Order.objects.get(key=pk)
        yAxis = list(map(
            lambda obj: obj[-4:], WorkOrder.objects.filter(Q(order=order) & ~Q(status__name='等待中')).values_list('number', flat=True)))
        data = map(lambda obj: {'x': ganteX(obj.startTime, obj), 'x2': ganteX(
            obj.endTime, obj), 'y': yAxis.index(obj.number[-4:]), 'partialFill': round(obj.events.all().count()/21, 2)}, WorkOrder.objects.filter(Q(order=order) & ~Q(status__name='等待中')))
        return Response({'yAxis': yAxis, 'data': data})


class ProductLineViewSet(viewsets.ModelViewSet):
    queryset = ProductLine.objects.all().order_by('-key')
    serializer_class = ProductLineSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'产线名称': obj.name, '产线类别': obj.lineType, '隶属车间': obj.workShop.name,
                                 '产线编号': obj.number, '产线状态': obj.state.name, '产线描述': obj.description}, ProductLine.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProcessRouteViewSet(viewsets.ModelViewSet):
    queryset = ProcessRoute.objects.all().order_by('-key')
    serializer_class = ProcessRouteSerializer

    @action(methods=['post'], detail=True)
    def deviceBanding(self, request, pk=None):
        params = request.data
        device = Device.objects.get(key=pk)
        if params['process'] != '':
            process = Process.objects.get(
                Q(name=params['process'], route__key=params['route']))
            device.process = process
        else:
            device.process = None
        device.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def deviceUnbanding(self, request):
        params = request.data
        for device in Device.objects.filter(Q(process__name=params['process'], process__route__key=params['route'])):
            device.process = None
            device.save()
        return Response('ok')

    @action(methods=['post'], detail=True)
    def process(self, request, pk=None):
        params = request.data
        list(map(lambda obj: updateDevice(obj), Device.objects.filter(
            Q(process__route__key=pk))))
        Process.objects.filter(
            route=ProcessRoute.objects.get(key=pk)).delete()
        orders = json.loads(params['value'])['linkDataArray']
        processes = json.loads(params['value'])['nodeDataArray']

        for i in range(len(processes)):
            process = Process()
            process.route = ProcessRoute.objects.get(key=pk)
            if i == len(processes)-1:
                proc = list(
                    filter(lambda obj: obj['key'] == orders[-1]['to'], processes))
                process.name = proc[0]['text']
            else:
                proc = list(
                    filter(lambda obj: obj['key'] == orders[i]['from'], processes))
                process.name = proc[0]['text']
            process.save()
        return Response('ok')

    @action(methods=['post'], detail=True)
    def processParams(self, request, pk=None):
        params = request.data
        processParam = ProcessParams()
        processParam.name = params['name']
        processParam.value = params['value']
        processParam.tagName = params['tagName']
        processParam.topLimit = params['topLimit']
        processParam.lowLimit = params['lowLimit']
        processParam.unit = '' if params['unit'] == '无' else params['unit']
        processParam.process = Process.objects.get(
            Q(name=params['process'], route__key=pk))
        processParam.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def upload(self, request):
        url = request.POST['url']
        route = request.POST['route']
        process = request.POST['process']
        pro = Process.objects.get(Q(name=process, route__key=route))
        f = request.FILES['file']
        with open(BASE_DIR+'/upload/picture/'+''.join(list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'), 'wb') as uf:
            for chunk in f.chunks():
                uf.write(chunk)
        pro.path = 'http://%s:8899/upload/picture/%s' % (url, ''.join(
            list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'))
        pro.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'工艺名称': obj.name, '工艺类别': obj.routeType, '工艺描述': obj.description, '创建人': obj.creator, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'),
                                 '包含工序': ('->').join(list(map(lambda obj: obj.name, Process.objects.filter(Q(route=obj))))), '详细数据': obj.data}, ProcessRoute.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'route']


class BottleViewSet(viewsets.ModelViewSet):
    queryset = Bottle.objects.all()
    serializer_class = BottleSerializer


class BottleStateViewSet(viewsets.ModelViewSet):
    queryset = BottleState.objects.all()
    serializer_class = BottleStateSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().order_by('-createTime')
    serializer_class = WorkOrderSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['number', 'status', 'bottle']

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'工单状态': obj.status.name, '工单编号': obj.number, '订单编号': obj.order.number, '工单瓶号': obj.bottle, '创建时间': obj.createTime.strftime(
            '%Y-%m-%d %H:%M:%S'), '开始时间': obj.startTime, '结束时间': obj.endTime, '工单描述': obj.description}, WorkOrder.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by('-key')
    serializer_class = StoreSerializer

    @action(methods=['post'], detail=True)
    def modeling(self, request, pk=None):
        params = json.loads(request.body)
        store = Store.objects.get(key=pk)
        storeType = store.productLine.lineType.name
        store.direction = params['direction']
        store.dimensions = params['dimensions']
        store.save()
        count = params['row']*params['column']
        if storeType == '电子装配':
            left = np.arange(
                0, count/2).reshape(params['row'], int(params['column']/2))
            right = np.arange(
                count/2, count).reshape(params['row'], int(params['column']/2))
            martix = np.hstack((left, right)).reshape(1, count)
            for i in np.ravel(martix):
                position = StorePosition()
                position.store = store
                position.number = '%s-%s' % (str(int(i)+1), pk)
                position.status = selectStatus(storeType, i, count)
                position.description = selectDescription(
                    storeType, i, count, params['row'], params['column'])
                position.save()
        else:
            for i in range(count):
                position = StorePosition()
                position.store = store
                position.number = '%s-%s' % (str(i+1), pk)
                position.status = selectStatus(storeType, i, count)
                position.description = selectDescription(
                    storeType, i, count, params['row'], params['column'])
                position.save()
                if storeType == '灌装':
                    pallet = Pallet()
                    pallet.position = StorePosition.objects.get(
                        number='%s-%s' % (str(i+1), pk))
                    pallet.number = str(i+1)
                    pallet.save()
        return Response('ok')

    @action(methods=['put'], detail=False)
    def positionGroup(self, request):
        params = request.data
        position = StorePosition.objects.get(
            Q(number=params['item'].split('/')[0]))
        position.description = params['value']
        position.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def counts(self, request):
        params = request.data
        count = Store.objects.filter(
            Q(storeType__name=params['storeType'], productLine__name=params['productLine'])).count()
        return Response(count)

    @action(methods=['post'], detail=False)
    def mwPosition(self, request):
        params = request.data
        content = StorePosition.objects.get(
            number=params['item'].split('/')[0]).content
        return Response(content)

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'仓库名称': obj.name, '隶属车间': obj.workShop.name, '使用产线': obj.productLine.name,
                                 '仓库编号': obj.number, '仓库类型': obj.storeType.name, '仓库规模': obj.dimensions}, Store.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class StoreTypeViewSet(viewsets.ModelViewSet):
    queryset = StoreType.objects.all()
    serializer_class = StoreTypeSerializer


class StorePositionViewSet(viewsets.ModelViewSet):
    queryset = StorePosition.objects.all()
    serializer_class = StorePositionSerializer


class OperateViewSet(viewsets.ModelViewSet):
    queryset = Operate.objects.all().order_by('-time')
    serializer_class = OperateSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    @action(methods=['get'], detail=False)
    def interviewChart(self, request):
        data = map(lambda obj: [dataX(obj.time.date()), dataY(
            obj.time)], Operate.objects.filter(Q(name='登陆系统')).order_by('time'))
        return Response([{'type': 'areaspline', 'name': '日访问量', 'data': reduce(lambda x, y: x if y in x else x+[y], [[], ]+list(data))}])

    @action(methods=['get'], detail=False)
    def operateChart(self, request):
        dikaer, series = [], []
        for x, y in product(range(10), range(10)):
            dikaer.append([x, y])
        data = [{'data': series}]
        operateList = Operate.objects.all().order_by('-time')
        for i in range(len(operateList) if len(operateList) <= 100 else 100):
            ope = {}
            ope['value'] = 1
            ope['x'] = dikaer[i][0]
            ope['y'] = dikaer[i][1]
            ope['operate'] = operateList[i].name
            ope['operator'] = operateList[i].operator
            ope['time'] = operateList[i].time.strftime('%Y-%m-%d %H:%M:%S')
            series.append(ope)

        return Response(data)


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-key')
    serializer_class = DeviceSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'设备名称': obj.name, '设备类型': obj.deviceType.name, '设备状态': list(DeviceState.objects.filter(Q(device=obj)))[-1].name, '所在工序': obj.process.name if obj.process else '', '设备编号': obj.number, '入库时间': obj.joinTime.strftime(
            '%Y-%m-%d %H:%M:%S'), '设备厂家': obj.factory, '出厂日期': obj.facTime, '厂家联系人': obj.facPeo, '厂家电话': obj.facPho}, Device.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['docType']

    @action(methods=['put'], detail=True)
    def counts(self, request, pk=None):
        params = request.data
        doc = Document.objects.get(key=pk)
        doc.count = params['count']+1
        doc.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def upload(self, request):
        up = request.POST['up']
        url = request.POST['url']
        f = request.FILES['file']
        with open(BASE_DIR+'/upload/document/'+''.join(list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'), 'wb') as uf:
            for chunk in f.chunks():
                uf.write(chunk)
        document = Document()
        document.up = up
        document.name = f.name
        document.path = 'http://%s:8899/upload/document/%s' % (url, ''.join(
            list(map(lambda obj: obj[0], pypinyin.pinyin(f.name, style=pypinyin.NORMAL)))).replace(' ', '').replace('）', ')'))
        document.save()
        operate = Operate()
        operate.name = '上传文档'
        operate.operator = up
        operate.save()
        return Response('ok')


class LineStateViewSet(viewsets.ModelViewSet):
    queryset = LineState.objects.all()
    serializer_class = LineStateSerializer


class DocTypeViewSet(viewsets.ModelViewSet):
    queryset = DocType.objects.all()
    serializer_class = DocTypeSerializer


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer


class DeviceStateViewSet(viewsets.ModelViewSet):
    queryset = DeviceState.objects.all()
    serializer_class = DeviceStateSerializer


class DeviceFaultViewSet(viewsets.ModelViewSet):
    queryset = DeviceFault.objects.all()
    serializer_class = DeviceFaultSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def list(self, request, *args, **kwargs):
        queryset = Material.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'mateType', 'store__name', 'store__productLine__lineType__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))

    def update(self, request, *args, **kwargs):
        params = request.data
        for i in range(params['count']):
            material = Material()
            material.name = params['name']
            material.size = params['size']
            material.unit = params['unit']
            material.mateType = '1' if params['mateType'] == '自制' else '2'
            material.store = Store.objects.get(name=params['store__name'])
            material.save()
        Material.objects.filter(Q(name=None)).delete()
        return Response('ok')

    def destroy(self, request, *args, **kwargs):
        params = request.data
        Material.objects.filter(Q(name=params['name'])).delete()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'物料名称': obj['name'], '物料规格': obj['size'], '基本单位': obj['unit'], '物料类型': '自制' if obj['mateType'] == '1' else '外采', '现有库存': obj['counts'], '存储仓库': Store.objects.get(
            key=obj['store']).name}, Material.objects.all().values('name').annotate(counts=Count('size')).values('name', 'size', 'counts', 'unit', 'mateType', 'store'))
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer

    def list(self, request, *args, **kwargs):
        queryset = Tool.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'toolType', 'store__name', 'store__productLine__lineType__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))

    def update(self, request, *args, **kwargs):
        params = request.data
        for i in range(params['count']):
            tool = Tool()
            tool.name = params['name']
            tool.size = params['size']
            tool.unit = params['unit']
            tool.toolType = '1' if params['toolType'] == '自制' else '2'
            tool.store = Store.objects.get(name=params['store__name'])
            tool.save()
        Tool.objects.filter(Q(name=None)).delete()
        return Response('ok')

    def destroy(self, request, *args, **kwargs):
        params = request.data
        Tool.objects.filter(Q(name=params['name'])).delete()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'工具名称': obj['name'], '工具规格': obj['size'], '基本单位': obj['unit'], '工具类型': '自制' if obj['toolType'] == '1' else '外采', '现有库存': obj['counts'], '存储仓库': Store.objects.get(
            key=obj['store']).name}, Tool.objects.all().values('name').annotate(counts=Count('size')).values('name', 'size', 'counts', 'unit', 'toolType', 'store'))
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class PalletViewSet(viewsets.ModelViewSet):
    queryset = Pallet.objects.all()
    serializer_class = PalletSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        content = [request.data['hole1Content'], request.data['hole2Content'], request.data['hole3Content'], request.data['hole4Content'],
                   request.data['hole5Content'], request.data['hole6Content'], request.data['hole7Content'], request.data['hole8Content'], request.data['hole9Content']]
        data = request.data.copy()
        data['rate'] = round(
            len(list(filter(lambda obj: obj != '', content)))/9, 2)
        position = instance.position
        if data['rate'] > 0:
            position.status = '3'
        if data['rate'] == 0.0:
            position.status = '4'
        position.save()
        serializer = self.get_serializer(
            instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-key')
    serializer_class = ProductSerializer

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        if params['model'] == 'product':
            excel = map(lambda obj: {'成品名称': obj.name, '成品编号': obj.number, '对应工单': obj.workOrder.number, '成品批次': obj.batch.strftime('%Y-%m-%d'), '质检结果': '合格' if obj.result == '1' else '不合格', '存放仓位': selectPosition(
                obj), '历史状态': ('->').join(list(map(lambda event: '%s/%s' % (event.time.strftime('%Y-%m-%d %H:%M:%S'), event.title), Event.objects.filter(Q(workOrder=obj.workOrder)))))}, Product.objects.all())
        if params['model'] == 'unqualified':
            excel = map(lambda obj: {'成品名称': obj.name, '成品编号': obj.number, '对应工单': obj.workOrder.number, '成品批次': obj.batch.strftime(
                '%Y-%m-%d'), '不合格原因': obj.reason, '存放仓位': selectPosition(obj)}, Product.objects.filter(result='2'))
        if params['model'] == 'qualAna':
            excel = Product.objects.filter(Q(workOrder__order__orderType__name=params['orderType'])).values('batch').annotate(日期=F(
                'batch'), 合格数=Count('result', filter=Q(result='1')), 不合格数=Count('result', filter=Q(result='2'))).values('日期', '合格数', '不合格数')
        if params['model'] == 'mateAna':
            if params['orderType'] == '灌装':
                excel = map(lambda obj: {'日期': obj['createTime'].strftime('%Y-%m-%d'), '瓶盖': obj['cap'], '红瓶': obj['rbot'], '绿瓶': obj['gbot'], '蓝瓶': obj['bbot'], '红粒': obj['reds'], '绿粒': obj['greens'], '蓝粒': obj['blues']}, Bottle.objects.all().values('createTime').annotate(cap=Count(
                    'color'), rbot=Count('color', filter=Q(color='红瓶')), gbot=Count('color', filter=Q(color='绿瓶')), bbot=Count('color', filter=Q(color='蓝瓶')), reds=Sum('red'), greens=Sum('green'), blues=Sum('blue')).values('createTime', 'cap', 'rbot', 'gbot', 'bbot', 'reds', 'greens', 'blues'))
            if params['orderType'] == '机加':
                excel = map(lambda obj: {'日期': obj['batch'].strftime('%Y-%m-%d'), '原料棒': obj['count']}, Product.objects.filter(Q(workOrder__order__orderType__name='机加')).values('batch').annotate(
                    count=Count('batch', filter=Q(workOrder__status__name='已完成'))).values('batch', 'count'))
            if params['orderType'] == '电子装配':
                materialDict = {}
                materials = Material.objects.filter(
                    Q(store__storeType__name='混合库', store__productLine__lineType__name='电子装配')).values('name', 'size').distinct()
                for material in materials:
                    materialDict[material['name']] = Sum('prodType__bom__contents__counts', filter=Q(
                        prodType__bom__contents__material=material['name']+'/'+material['size']))
                excel = Product.objects.filter(Q(workOrder__order__orderType__name='电子装配')).values(
                    'batch').annotate(**materialDict).values('batch', *materialDict.keys())
        if params['model'] == 'powerAna':
            excel = Product.objects.filter(Q(workOrder__order__orderType__name=params['orderType'])).values('batch').annotate(日期=F('batch'), 预期产量=Count('number'), 实际产量=Count('number', filter=Q(
                workOrder__status__name='已完成')), 合格率=Cast(Count('number', filter=Q(result='1')), output_field=FloatField()) / Count('number', output_field=FloatField())).values('日期', '预期产量', '实际产量', '合格率')
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all().order_by('-key')
    serializer_class = ProductTypeSerializer

    @action(methods=['put'], detail=False)
    def dataViews(self, request):
        params = request.data
        product = ProductType.objects.filter(
            Q(orderType__name=params['orderType']))
        productDict, fieldDict, materialStr = {}, {}, ''
        for field in apps.get_model('app', 'Bottle')._meta.fields:
            fieldDict[field.verbose_name] = field.name
        for prod in product:
            productDict[prod.name] = Count('workOrders__workOrder__name', filter=Q(
                workOrders__workOrder__name=prod.name)) if params['orderType'] != '灌装' else Count('bottles', filter=Q(bottles__color=prod.name))
            if params['orderType'] == '灌装':
                boms = BOMContent.objects.filter(
                    Q(bom__product=prod) & ~Q(material__icontains=prod.name) & ~Q(material__icontains='盖'))
                for bom in boms:
                    materialStr = materialStr+bom.material.split('/')[0]+','
                for mat in list(filter(lambda obj: obj != '', list(set(materialStr.split(','))))):
                    productDict[prod.name+mat] = Avg(
                        'bottles__%s' % fieldDict[mat], filter=Q(bottles__color=prod.name))

        orders = Order.objects.filter(
            Q(status=OrderStatus.objects.get(name='已排产'), orderType=OrderType.objects.get(name=params['orderType']))).values('number').annotate(订单编号=F('number'), 订单批次=F('batch'), 排产时间=F('scheduling'), 订单状态=F('status__name'),  **productDict).values('订单编号', '订单批次', '排产时间', '订单状态', *productDict.keys())

        dv = DataView.objects.all()[0]
        if params['orderType'] == '机加':
            dv.mwContent = formatSql(orders.query.__str__().split(' '))
        if params['orderType'] == '电子装配':
            dv.eaContent = formatSql(orders.query.__str__().split(' '))
        if params['orderType'] == '灌装':
            dv.gzContent = formatSql(orders.query.__str__().split(' '))
        dv.save()
        return Response('ok')

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'产品名称': obj.name, '订单类型': obj.orderType.name,
                                 '产品编号': obj.number, '产品容差': obj.errorRange}, ProductType.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class DataViewViewSet(viewsets.ModelViewSet):
    queryset = DataView.objects.all()
    serializer_class = DataViewSerializer


class ProductStandardViewSet(viewsets.ModelViewSet):
    queryset = ProductStandard.objects.all().order_by('-key')
    serializer_class = ProductStandardSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        product = Product.objects.get(
            Q(workOrder__number=request.data['product'].split('/')[1]))
        product.result = '1' if str(request.data['result']) == '1' else '2'
        product.reason = '%s%s' % (
            request.data['name'], request.data['realValue'])
        product.save()

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def export(self, request):
        params = request.data
        excel = map(lambda obj: {'产品名称': obj.product.name, '标准名称': obj.name, '预期结果': obj.expectValue,
                                 '实际结果': obj.realValue, '检测结果': '合格' if obj.result == '1' else '不合格'}, ProductStandard.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
