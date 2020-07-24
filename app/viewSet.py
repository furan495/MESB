import os
import json
import datetime
import pypinyin
import numpy as np
import pandas as pd
from app.utils import *
from app.models import *
from functools import reduce
from django.apps import apps
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

colDict = {'ForeignKey': 'select', 'CharField': 'text',
           'DateTimeField': 'text', 'FloatField': 'number', 'OneToOneField': 'select', 'IntegerField': 'number', 'DateField': 'text'}


class WorkShopViewSet(viewsets.ModelViewSet):
    queryset = WorkShop.objects.all()
    serializer_class = WorkShopSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'WorkShop')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True, 'width': '10%' if field.name != 'descriptions' else None})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'车间编号': obj.number, '车间名称': obj.name,
                                 '车间描述': obj.descriptions}, WorkShop.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'BOM')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        columns.append({'title': 'BOM描述', 'dataIndex': 'contents',
                        'inputType': 'text', 'editable': False, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
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

    @action(methods=['get'], detail=False)
    def charts(self, request):
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


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('-key')
    serializer_class = RoleSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Role')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True, 'width': '10%' if field.name == 'name' else None})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'角色名': obj.name,
                                 '权限范围': obj.authority}, Role.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-key')
    serializer_class = CustomerSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Customer')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'客户名称': obj.name, '客户编号': obj.number, '联系电话': obj.phone,
                                 '客户等级': obj.level, '公司': obj.company}, Customer.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'User')._meta.fields:
            if field.name != 'key' and field.name != 'password':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': 'select' if field.name == 'gender' else colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def login(self, request):
        res = ''
        params = request.query_params
        user = User.objects.get(phone=params['phone'])
        if user.password == params['password']:
            res = UserSerializer(user).data
        else:
            res = 'err'
        return Response({'res': res, 'count': User.objects.filter(Q(status='在线')).count()})

    @action(methods=['get'], detail=False)
    def logout(self, request):
        params = request.query_params
        user = User.objects.get(Q(phone=params['phone']))
        user.status = '离线'
        user.save()
        return Response('ok')

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        params = request.data
        user = User.objects.get(key=pk)
        user.status = params['status']
        user.save()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'角色': obj.role.name, '姓名': obj.name, '性别': obj.gender,
                                 '部门': obj.department.name if obj.department else '', '职位': obj.post, '代号': obj.phone}, User.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-key')
    serializer_class = OrderSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Order')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['put'], detail=True)
    def preScheduling(self, request, pk=None):
        res, info = 'ok', ''
        params = request.data
        order = self.get_object()
        orderType = params['orderType']
        line = ProductLine.objects.get(name=params['line'])
        route = ProcessRoute.objects.get(name=params['route'])
        if orderType == line.lineType.name and orderType == route.routeType.name:
            products = order.products.all().values_list(
                'prodType__name', flat=True).distinct()
            for product in products:
                count = order.products.all().filter(Q(prodType__name=product)).count()
                if count > StorePosition.objects.filter(Q(description__icontains=product, status='2')).count():
                    res = 'err'
                    info = '%s仓位不足，无法排产' % product
                else:
                    for bom in BOMContent.objects.filter(Q(bom__product__name=product)):
                        counts = bom.counts if bom.counts else 1
                        if count*counts > StorePosition.objects.filter(Q(description__icontains=bom.material.split('/')[0], status='1')).count():
                            res = 'err'
                            info = '%s不足，无法排产' % bom.material.split('/')[0]
        else:
            res = 'err'
            info = '产线或工艺不符，无法排产'

        return Response({'res': res, 'info': info})

    @action(methods=['post'], detail=True)
    def scheduling(self, request, pk=None):
        order = self.get_object()
        order.status = CommonStatus.objects.get(name='已排产')
        order.batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order.scheduling = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order.save()
        products = order.products.all()
        processes = order.route.processes.all()
        for product, index in zip(products, range(products.count())):
            for process in processes:
                workOrder = WorkOrder()
                workOrder.product = product
                workOrder.process = process
                workOrder.status = CommonStatus.objects.get(name='等待中')
                workOrder.number = str(time.time()*1000000)[:16]
                workOrder.save()

            product.number = str(time.time()*1000000)[:16]

            inPosition = StorePosition.objects.filter(
                Q(description__icontains=product, store__storeType__name='成品库', status='2') | Q(description__icontains=product, store__storeType__name='混合库', status='2')).first()
            inPosition.status = '1'
            inPosition.content = '%s-%s号位' % (
                inPosition.store.name, inPosition.number)
            inPosition.save()

            product.position = inPosition
            product.status = CommonStatus.objects.get(name='已排产')
            product.save()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'订单类别': obj.orderType.name, '选用工艺': obj.route.name, '订单状态': obj.status.name, '创建人': obj.creator, '目标客户': obj.customer.name,
                                 '订单编号': obj.number, '创建时间': obj.createTime.strftime('%Y-%m-%d %H:%M:%S'), '排产时间': obj.scheduling, '订单批次': obj.batch, '订单描述': obj.description}, Order.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProductLineViewSet(viewsets.ModelViewSet):
    queryset = ProductLine.objects.all().order_by('-key')
    serializer_class = ProductLineSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'ProductLine')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'产线名称': obj.name, '产线类别': obj.lineType.name, '隶属车间': obj.workShop.name,
                                 '产线编号': obj.number, '产线描述': obj.description}, ProductLine.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProcessRouteViewSet(viewsets.ModelViewSet):
    queryset = ProcessRoute.objects.all().order_by('-key')
    serializer_class = ProcessRouteSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'ProcessRoute')._meta.fields:
            if field.name != 'key' and field.name != 'data':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

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

    @action(methods=['post'], detail=True)
    def process(self, request, pk=None):
        params = request.data
        processes = json.loads(params['value'])['nodeDataArray']
        if Process.objects.filter(Q(route__key=pk)).count() == 0:
            for proc in processes:
                process = Process()
                process.route = ProcessRoute.objects.get(key=pk)
                process.name = proc['text']
                process.save()
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

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
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

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Process')._meta.fields:
            if field.name != 'key' and field.name != 'path':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def column(self, request):
        column = [{'title': '产品名称', 'dataIndex': 'name',
                   'inputType': 'text', 'editable': False, 'ellipsis': True}]
        for process in Process.objects.all():
            column.append({'title': '%s开始' % process.name,
                           'dataIndex': 'start%s' % process.number, 'inputType': 'text', 'editable': False, 'ellipsis': True})
            column.append({'title': '%s结束' % process.name,
                           'dataIndex': 'stop%s' % process.number, 'inputType': 'text', 'editable': False, 'ellipsis': True})
        return Response(column)


class DeviceBaseViewSet(viewsets.ModelViewSet):
    queryset = DeviceBase.objects.all()
    serializer_class = DeviceBaseSerializer

    def create(self, request, *args, **kwargs):
        params = request.data
        if 'typeNum' in params.keys():
            devices = Device.objects.filter(
                Q(typeNumber=params['typeNum'], deviceType__name=params['type']))
        else:
            devices = Device.objects.filter(Q(deviceType__name=params['type']))
        for device in devices:
            base = DeviceBase()
            base.device = device
            base.name = params['name']
            base.value = params['value']
            base.save()
        return Response('ok')


class CommonStatusViewSet(viewsets.ModelViewSet):
    queryset = CommonStatus.objects.all()
    serializer_class = CommonStatusSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().order_by('-createTime')
    serializer_class = WorkOrderSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['number', 'status']

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'WorkOrder')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'工单状态': obj.status.name, '工单编号': obj.number, '订单编号': obj.order.number, '创建时间': obj.createTime.strftime(
            '%Y-%m-%d %H:%M:%S'), '开始时间': obj.startTime, '结束时间': obj.endTime, '工单描述': obj.description}, WorkOrder.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by('-key')
    serializer_class = StoreSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Store')._meta.fields:
            if field.name != 'key' and field.name != 'path':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': 'select' if field.name == 'direction' or field.name == 'origin' else colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.positions.all().delete()

        rows = request.data['rows']
        columns = request.data['columns']
        counts = rows*columns
        lineType = ProductLine.objects.get(
            name=request.data['productLine']).lineType.name

        if lineType == '电子装配':
            left = np.arange(
                0, counts/2).reshape(rows, int(columns/2))
            right = np.arange(
                counts/2, counts).reshape(rows, int(columns/2))
            matrix = np.hstack((left, right))
            for i in np.ravel(np.flip(matrix, axis=0)):
                position = StorePosition()
                position.store = instance
                position.number = str(int(i)+1)
                position.status = '2'
                position.description = ''
                position.save()
        else:
            for i in range(counts):
                position = StorePosition()
                position.store = instance
                position.number = str(i+1)
                position.status = '2'
                position.description = ''
                position.save()
                if lineType == '灌装' and request.data['storeType'] == '成品库':
                    pallet = Pallet()
                    pallet.position = StorePosition.objects.get(
                        number=str(i+1), store=instance)
                    pallet.number = str(i+1)
                    pallet.save()

                    for j in range(9):
                        hole = PalletHole()
                        hole.number = str(j+1)
                        hole.pallet = pallet
                        hole.save()

        if request.data['origin'] == '左上起点':
            if request.data['direction'] == '行优先':
                numbers = np.arange(1, counts+1)
            else:
                numbers = np.arange(
                    1, counts+1).reshape(columns, rows).T
            for pos, num in zip(instance.positions.all(),  np.ravel(numbers)):
                pos.number = num
                pos.save()
        if request.data['origin'] == '左下起点':
            if request.data['direction'] == '行优先':
                numberMatrix = np.arange(
                    1, counts+1).reshape(rows, columns)
            else:
                numberMatrix = np.arange(
                    1, counts+1).reshape(columns, rows).T
            numberFlip = np.flip(numberMatrix, axis=0)
            for pos, num in zip(instance.positions.all(), np.ravel(numberFlip)):
                pos.number = num
                pos.save()

        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def counts(self, request):
        params = request.data
        count = Store.objects.filter(
            Q(storeType__name=params['storeType'], productLine__name=params['productLine'])).count()
        return Response(count)

    @action(methods=['put'], detail=True)
    def positions(self, request, pk=None):
        params = request.data
        if params['product'] != '':
            for key in params['contents']:
                pos = StorePosition.objects.get(key=key)
                pos.description = params['product']
                pos.save()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'仓库名称': obj.name, '隶属车间': obj.workShop.name, '使用产线': obj.productLine.name,
                                 '仓库编号': obj.number, '仓库类型': obj.storeType.name, '仓库行数': obj.rows, '仓库列数': obj.columns, '排向优先': obj.direction}, Store.objects.all())
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
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Operate')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def interviewChart(self, request):
        data = map(lambda obj: [dataX(obj.time.date()), dataY(
            obj.time)], Operate.objects.filter(Q(name='登录系统')).order_by('time'))
        return Response([{'type': 'areaspline', 'name': '日访问量', 'data': reduce(lambda x, y: x if y in x else x+[y], [[], ]+list(data))}])


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-key')
    serializer_class = DeviceSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Device')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['put'], detail=True)
    def unbanding(self, request, pk):
        device = Device.objects.get(key=pk)
        device.process = None
        device.save()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def numbers(self, request):
        params = request.query_params
        return Response(Device.objects.filter(Q(deviceType__name=params['number'])).values_list('typeNumber', flat=True).distinct())

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'设备名称': obj.name, '设备类型': obj.deviceType.name, '所在工序': obj.process.name if obj.process else '',
                                 '设备编号': obj.number, '设备厂家': obj.factory, '设备型号': obj.typeNumber}, Device.objects.all())
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


class DocTypeViewSet(viewsets.ModelViewSet):
    queryset = DocType.objects.all()
    serializer_class = DocTypeSerializer


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer

    def list(self, request, *args, **kwargs):
        return Response(DeviceType.objects.all().values_list('name', flat=True))


class DeviceStateViewSet(viewsets.ModelViewSet):
    queryset = DeviceState.objects.all()
    serializer_class = DeviceStateSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def list(self, request, *args, **kwargs):
        queryset = Material.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'store__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Material')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': 'store__name' if field.name == 'store' else field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
                if field.name == 'unit':
                    columns.append({'title': '现有库存', 'dataIndex': 'counts',
                                    'inputType': 'number', 'editable': True, 'ellipsis': True})
        return Response(columns)

    def update(self, request, *args, **kwargs):
        params = request.data
        for i in range(params['counts']):
            material = Material()
            material.name = params['name']
            material.size = params['size']
            material.unit = params['unit']
            material.store = Store.objects.get(name=params['store__name'])
            material.save()
        Material.objects.filter(Q(name=None)).delete()
        return Response('ok')

    def destroy(self, request, *args, **kwargs):
        params = request.data
        Material.objects.filter(Q(name=params['name'])).delete()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def materialChart(self, request):
        params = request.query_params
        start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
        stop = datetime.datetime.strptime(
            params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
        data = materialChart(params['order'], start, stop, all=False)
        return Response(data)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'物料名称': obj['name'], '物料规格': obj['size'], '基本单位': obj['unit'], '物料类型': obj['mateType'], '现有库存': obj['counts'], '存储仓库': Store.objects.get(
            key=obj['store']).name}, Material.objects.all().values('name').annotate(counts=Count('size')).values('name', 'size', 'counts', 'unit', 'mateType', 'store'))
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer

    def list(self, request, *args, **kwargs):
        queryset = Tool.objects.all().values('name').annotate(
            counts=Count('size')).values('name', 'size', 'counts', 'unit', 'store__name')
        return Response(list(map(lambda obj: addkey(obj, list(queryset)), list(queryset))))

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Tool')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': 'store__name' if field.name == 'store' else field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
                if field.name == 'unit':
                    columns.append({'title': '现有库存', 'dataIndex': 'counts',
                                    'inputType': 'number', 'editable': True, 'ellipsis': True})
        return Response(columns)

    def update(self, request, *args, **kwargs):
        params = request.data
        for i in range(params['counts']):
            tool = Tool()
            tool.name = params['name']
            tool.size = params['size']
            tool.unit = params['unit']
            tool.store = Store.objects.get(name=params['store__name'])
            tool.save()
        Tool.objects.filter(Q(name=None)).delete()
        return Response('ok')

    def destroy(self, request, *args, **kwargs):
        params = request.data
        Tool.objects.filter(Q(name=params['name'])).delete()
        return Response('ok')

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'工具名称': obj['name'], '工具规格': obj['size'], '基本单位': obj['unit'], '工具类型': obj['toolType'], '现有库存': obj['counts'], '存储仓库': Store.objects.get(
            key=obj['store']).name}, Tool.objects.all().values('name').annotate(counts=Count('size')).values('name', 'size', 'counts', 'unit', 'toolType', 'store'))
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class PalletViewSet(viewsets.ModelViewSet):
    queryset = Pallet.objects.all()
    serializer_class = PalletSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position']

    @action(methods=['get'], detail=False)
    def numbers(self, request):
        counts = Product.objects.filter(Q(status__name='已排产')).count()
        pallets = Pallet.objects.filter(Q(rate__lte=0.33)).values_list(
            'number', flat=True)[:np.ceil(counts/9)]
        return Response(pallets)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-key')
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['number']

    def create(self, request, *args, **kwargs):
        params = request.data
        for i in range(params['counts']):
            product = Product()
            product.order = Order.objects.get(key=params['key'])
            product.batch = datetime.datetime.now().strftime('%Y-%m-%d')
            product.prodType = ProductType.objects.get(name=params['product'])
            product.save()

            standard = ProductStandard()
            standard.name = '重量'
            standard.expectValue = '50'
            standard.product = product
            standard.save()

            for bom in BOMContent.objects.filter(Q(bom__product__name=params['product'])):
                pi = ProductInfo()
                pi.product = product
                pi.name = bom.material
                pi.value = bom.counts if bom.counts else params[bom.material.split(
                    '/')[1]]
                pi.save()

        return Response('ok')

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'Product')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def powerChart(self, request):
        params = request.query_params
        start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
        stop = datetime.datetime.strptime(
            params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
        data = powerChart(params['order'], start, stop, all=False)
        return Response(data)

    @action(methods=['get'], detail=False)
    def qualityChart(self, request):
        params = request.query_params
        start = datetime.datetime.strptime(params['start'], '%Y/%m/%d')
        stop = datetime.datetime.strptime(
            params['stop'], '%Y/%m/%d')+datetime.timedelta(hours=24)
        data = qualityChart(params['order'], start, stop, all=False)
        return Response(data)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        if params['model'] == 'product':
            excel = map(lambda obj: {'成品名称': obj.name, '成品编号': obj.number, '对应订单': obj.order.number, '成品批次': obj.batch.strftime(
                '%Y-%m-%d'), '质检结果':  obj.result, '存放仓位': obj.position.content}, Product.objects.all())
        if params['model'] == 'unqualified':
            excel = map(lambda obj: {'成品名称': obj.name, '成品编号': obj.number, '对应订单': obj.order.number, '成品批次': obj.batch.strftime(
                '%Y-%m-%d'), '不合格原因': obj.reason, '存放仓位': obj.position.content}, Product.objects.filter(result='不合格'))
        if params['model'] == 'qualityChart':
            excel = Product.objects.filter(Q(order__orderType__name=params['orderType'])).values('batch').annotate(日期=F(
                'batch'), 合格数=Count('number', filter=Q(result='合格')), 不合格数=Count('number', filter=Q(result='不合格'))).values('日期', '合格数', '不合格数')
        if params['model'] == 'materialChart':
            material = {}
            querySet = ProductInfo.objects.filter(
                Q(product__order__orderType__name=params['orderType'])).values('product__batch')
            for mat in BOMContent.objects.all().values_list('material', flat=True).distinct():
                material[mat.split('/')[0]] = Sum('value', filter=Q(name=mat))
            excel = querySet.annotate(
                日期=F('product__batch'), **material).values('日期', *material.keys())

        if params['model'] == 'powerChart':
            excel = Product.objects.filter(Q(order__orderType__name=params['orderType'])).values('batch').annotate(日期=F('batch'), 预期产量=Count('number'), 实际产量=Count('number', filter=Q(
                status__name='入库')), 合格率=Cast(Count('number', filter=Q(result='合格')), output_field=FloatField()) / Count('number', filter=Q(status__name='入库'), output_field=FloatField())).values('日期', '预期产量', '实际产量', '合格率')
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all().order_by('-key')
    serializer_class = ProductTypeSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'ProductType')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'产品名称': obj.name, '订单类型': obj.orderType.name,
                                 '产品编号': obj.number, '产品容差': obj.errorRange}, ProductType.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class ProductStandardViewSet(viewsets.ModelViewSet):
    queryset = ProductStandard.objects.all().order_by('-key')
    serializer_class = ProductStandardSerializer

    @action(methods=['get'], detail=False)
    def columns(self, request):
        columns = []
        for field in apps.get_model('app', 'ProductStandard')._meta.fields:
            if field.name != 'key':
                columns.append({'title': field.verbose_name, 'dataIndex': field.name, 'inputType': colDict[type(
                    field).__name__], 'editable': field.editable, 'ellipsis': True})
        return Response(columns)

    @action(methods=['get'], detail=False)
    def export(self, request):
        params = request.query_params
        excel = map(lambda obj: {'产品名称': obj.product.name, '标准名称': obj.name, '预期结果': obj.expectValue,
                                 '实际结果': obj.realValue, '检测结果': obj.result}, ProductStandard.objects.all())
        df = pd.DataFrame(list(excel))
        df.to_excel(BASE_DIR+'/upload/export/export.xlsx')
        return Response('http://%s:8899/upload/export/export.xlsx' % params['url'])


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class ProductInfoViewSet(viewsets.ModelViewSet):
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer


class PalletHoleViewSet(viewsets.ModelViewSet):
    queryset = PalletHole.objects.all()
    serializer_class = PalletHoleSerializer
