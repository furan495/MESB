import os
import json
import datetime
import pypinyin
import numpy as np
from app.utils import *
from app.models import *
from django.apps import apps
from app.serializers import *
from django.db.models import Q, F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.aggregates import Count, Sum, Max, Min, Avg

# Create your views here.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorkShopViewSet(viewsets.ModelViewSet):
    queryset = WorkShop.objects.all().order_by('-createTime')
    serializer_class = WorkShopSerializer


class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all().order_by('-createTime')
    serializer_class = BOMSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.parent:
            Organization.objects.filter(Q(key=instance.key) | Q(
                parent=instance.name)).delete()
        else:
            Organization.objects.all().delete()
        return Response({'res': 'succ'}, status=200)

    @action(methods=['get'], detail=False)
    def queryOrganization(self, request):
        data = list(map(lambda obj: {
            'key': obj.key,
            'title': obj.name,
            'children': loopOrganization(obj.name)
        }, Organization.objects.filter(Q(parent=None))))

        series = list(map(lambda obj: [obj.parent if obj.parent else obj.name, obj.name],
                          Organization.objects.filter(~Q(parent=None))))

        return Response({'tree': data, 'series': series, 'parent': list(map(lambda obj: [obj.key, obj.name], Organization.objects.all()))})


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


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-key')
    serializer_class = CustomerSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['post'], detail=False)
    def loginCheck(self, request):
        res = ''
        params = request.data
        user = User.objects.get(phone=params['phone'])
        if user.password == params['password']:
            res = UserSerializer(user).data
        else:
            res = 'err'
        return Response({'res': res, 'count': User.objects.filter(Q(status='2')).count()})

    @action(methods=['post'], detail=False)
    def logoutUser(self, request):
        params = request.data
        user = User.objects.get(Q(phone=params['phone']))
        user.status = '1'
        user.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=True)
    def updateUserState(self, request, pk=None):
        params = json.loads(request.body)
        user = User.objects.get(key=pk)
        user.status = params['status']
        user.save()
        return Response({'res': 'ok'})


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-key')
    serializer_class = OrderSerializer

    @action(methods=['post'], detail=True)
    def addBottle(self, request, pk=None):
        params = request.data
        for count in range(params['counts']):
            bottle = Bottle()
            bottle.order = Order.objects.get(key=pk)
            bottle.number = ''
            bottle.color = params['color']
            bottle.red = params['red']
            bottle.green = params['green']
            bottle.blue = params['blue']
            bottle.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=True)
    def splitCheck(self, request, pk=None):
        res, info = 'ok', ''
        params = request.data
        line = ProductLine.objects.get(name=params['line'])
        route = ProcessRoute.objects.get(name=params['route'])
        if params['orderType'] == line.lineType.name and params['orderType'] == route.routeType.name:
            if params['orderType'] == '灌装':
                particles, fieldDict = {}, {}
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
                        info = '%s不足，无法排产' % bottle
                    for particle in desc.split(',')[1:-1]:
                        particles[particle.split(':')[0]] = Sum(
                            'bottles__%s' % fieldDict[particle.split(':')[0]])
                    particleCounts = Order.objects.filter(key=pk).annotate(
                        **particles).values(*particles.keys())
                    for parti in particleCounts[0].keys():
                        try:
                            occupyPar = Order.objects.filter(Q(status__name='已排产', order__orderType__name='灌装')).annotate(counts=Sum(
                                'bottles__%s' % fieldDict[particle.split(':')[0]])).values('counts')[0]['counts']
                        except:
                            occupyPar = 0
                        if Material.objects.filter(Q(name=parti)).count()-occupyPar < particleCounts[0][parti]:
                            res = 'err'
                            info = '%s不足，无法排产' % parti
            if params['orderType'] == '机加':
                count = 0
                descriptions = params['description']
                for desc in descriptions.split(';')[:-1]:
                    count = count+int(desc.split('x')[1])
                occupy = WorkOrder.objects.filter(
                    Q(order__status__name='已排产', order__orderType__name='机加')).count()
                if StorePosition.objects.filter(
                        Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='3', description='原料')).count() < count or Material.objects.filter(Q(store__storeType__name='混合库', store__productLine__lineType__name=params['orderType'])).count()-occupy < count:
                    res = 'err'
                    info = '原料不足，无法排产'
            if params['orderType'] == '电子装配':
                eaOutPosition, eaInPosition = {}, {}
                for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                    eaOutPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name)).count()
                    eaInPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name)).count()
                descriptions = params['description']
                materialStr, materialDict = '', {}
                for desc in descriptions.split(';')[:-1]:
                    product = desc.split('x')[0]
                    productCount = desc.split('x')[1]
                    bom = BOM.objects.get(Q(product__name=product))
                    matStr = ','.join(
                        list(map(lambda obj: obj.material, bom.contents.all())))+','
                    materialStr = materialStr + matStr
                    if eaOutPosition[product] < int(productCount):
                        res = 'err'
                        info = '%s原料底座不足，无法排产' % product
                    if eaInPosition[product] < int(productCount):
                        res = 'err'
                        info = '%s成品仓位不足，无法排产' % product
                for material in list(set(materialStr.split(',')))[1:]:
                    materialDict[material.split('/')[0]] = 0
                for desc in descriptions.split(';')[:-1]:
                    count = desc.split('x')[1]
                    product = desc.split('x')[0]
                    bom = BOM.objects.get(Q(product__name=product))
                    for mat in bom.contents.all():
                        counts = mat.counts*int(count)
                        materialDict[mat.material.split(
                            '/')[0]] = materialDict[mat.material.split('/')[0]] + counts
                for mat in list(set(materialStr.split(',')))[1:]:
                    try:
                        bomContents = BOMContent.objects.filter(
                            Q(bom__product__products__workOrder__order__status__name='已排产', bom__product__products__workOrder__order__orderType__name='电子装配')).values('material').distinct().annotate(counts=Sum('counts', filter=Q(material=mat))).values('counts')
                        occupy = list(filter(lambda obj: obj['counts'] != None, bomContents))[
                            0]['counts']
                    except:
                        occupy = 0
                    if Material.objects.filter(Q(name=mat.split('/')[0], size=mat.split('/')[1])).count()-occupy < materialDict[mat.split('/')[0]]:
                        res = 'err'
                        info = '%s不足，无法排产' % mat
            else:
                pass
        else:
            res = 'err'
            info = '产线或工艺不符，无法排产'

        return Response({'res': res, 'info': info})

    @action(methods=['post'], detail=True)
    def orderSplit(self, request, pk=None):
        params = request.data
        order = Order.objects.get(key=pk)
        orderDesc = params['description'].split(';')
        order.status = OrderStatus.objects.get(name='已排产')
        order.batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order.scheduling = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                        workOrder.number = random.randint(0, 255)
                        workOrder.status = WorkOrderStatus.objects.get(
                            name='等待中')
                        workOrder.description = description.split('x')[0]
                        workOrder.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=False)
    def bandProduct(self, request):
        params = request.data
        workOrder = WorkOrder.objects.filter(
            Q(order__number=params['number']))
        outPos = list(StorePosition.objects.filter(
            Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='3', description__icontains='原料')))[:workOrder.count()]
        outPosition = list(map(lambda obj: obj.number.split('-')[0], outPos))
        inPos = list(StorePosition.objects.filter(
            Q(store__productLine__lineType__name=params['orderType'], store__storeType__name='混合库', status='4', description__icontains='成品')).order_by('-key'))[:workOrder.count()]
        inPosition = list(map(lambda obj: obj.number.split('-')[0], inPos))

        eaOutPosition, eaInPosition = {}, {}

        for i in range(workOrder.count()):
            if params['orderType'] == '电子装配':
                for pro in ProductType.objects.filter(Q(orderType__name='电子装配')):
                    eaOutPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='3', description__icontains='%s原料' % pro.name))
                    eaInPosition[pro.name] = StorePosition.objects.filter(
                        Q(store__productLine__lineType__name='电子装配', store__storeType__name='混合库', status='4', description__icontains='%s成品' % pro.name))
            product = Product()
            product.name = workOrder[i].description
            product.number = str(time.time()*1000000)
            product.workOrder = workOrder[i]
            product.outPos = outPosition[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0].number.split(
                '-')[0]
            product.inPos = inPosition[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0].number.split(
                '-')[0]
            product.prodType = ProductType.objects.get(
                Q(orderType__name=params['orderType'], name__icontains=workOrder[i].description.split('x')[0]))
            product.save()

            outP = outPos[i] if params['orderType'] == '机加' else eaOutPosition[workOrder[i].description][0]
            outP.status = '4'
            outP.save()
            inP = inPos[i] if params['orderType'] == '机加' else eaInPosition[workOrder[i].description][0]
            inP.status = '3'
            inP.save()

            standard = ProductStandard()
            standard.name = '外观'
            standard.expectValue = '合格'
            standard.product = product
            standard.save()
        return Response({'res': 'ok'})


class ProductLineViewSet(viewsets.ModelViewSet):
    queryset = ProductLine.objects.all().order_by('-key')
    serializer_class = ProductLineSerializer


class ProcessRouteViewSet(viewsets.ModelViewSet):
    queryset = ProcessRoute.objects.all().order_by('-key')
    serializer_class = ProcessRouteSerializer

    @action(methods=['post'], detail=True)
    def deviceBand(self, request, pk=None):
        params = request.data
        device = Device.objects.get(key=pk)
        if params['process'] != '':
            process = Process.objects.get(
                Q(name=params['process'], route__key=params['route']))
            device.process = process
        else:
            device.process = None
        device.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=False)
    def deviceUnband(self, request):
        params = request.data
        for device in Device.objects.filter(Q(process__name=params['process'], process__route__key=params['route'])):
            device.process = None
            device.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=True)
    def updateProcessByRoute(self, request, pk=None):
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
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=True)
    def processParamsSetting(self, request, pk=None):
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
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=False)
    def uploadPic(self, request):
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
        return Response({'res': 'ok'})


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


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by('-key')
    serializer_class = StoreSerializer

    @action(methods=['post'], detail=True)
    def createStore(self, request, pk=None):
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
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=False)
    def positionGroup(self, request):
        params = request.data
        position = StorePosition.objects.get(
            Q(number=params['item'].split('/')[0]))
        position.description = params['value']
        position.save()
        return Response({'res': 'ok'})

    @action(methods=['post'], detail=False)
    def queryStores(self, request):
        params = request.data
        gz = Store.objects.filter(
            Q(storeType__name=params['type'], workShop__name=params['shop'], productLine__name=params['line'])).count()
        mw = Store.objects.filter(
            Q(storeType__name=params['type'], workShop__name=params['shop'], productLine__name=params['line'])).count()
        ea = Store.objects.filter(
            Q(storeType__name=params['type'], workShop__name=params['shop'], productLine__name=params['line'])).count()
        return Response({'gz': gz, 'mw': mw, 'ea': ea})


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


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-key')
    serializer_class = DeviceSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['docType']

    @action(methods=['post'], detail=True)
    def updateCount(self, request, pk=None):
        params = request.data
        doc = Document.objects.get(key=pk)
        doc.count = params['count']+1
        doc.save()
        return Response({'res': 'ok'})

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
        return Response({'res': 'ok'})


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
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'mateType', 'store__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer

    def list(self, request, *args, **kwargs):
        queryset = Tool.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'toolType', 'store__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))


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


class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all().order_by('-key')
    serializer_class = ProductTypeSerializer

    @action(methods=['post'], detail=False)
    def updateDataView(self, request):
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
        if params['orderType'] != '机加':
            dv.mwContent = formatSql(orders.query.__str__().split(' '))
        if params['orderType'] == '电子装配':
            dv.eaContent = formatSql(orders.query.__str__().split(' '))
        if params['orderType'] == '灌装':
            dv.gzContent = formatSql(orders.query.__str__().split(' '))
        dv.save()
        return Response({'res': 'ok'})


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


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
