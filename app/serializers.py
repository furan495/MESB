import time
from app.models import *
from django.db.models import Q
from rest_framework import serializers


class WorkShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShop
        fields = ('key', 'name', 'number',
                  'descriptions', 'createTime')


class OrganizationSerializer(serializers.ModelSerializer):

    level = serializers.SlugRelatedField(
        queryset=OrgaLevel.objects.all(), label='组织等级', slug_field='name', required=False)

    class Meta:
        model = Organization
        fields = ('key', 'name', 'level', 'parent', 'duty')


class OrgaLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrgaLevel
        fields = ('key', 'name')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('key', 'name', 'authority')


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ('key', 'name')


class WorkOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderStatus
        fields = ('key', 'name')


class OrderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderType
        fields = ('key', 'name')


class StoreTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreType
        fields = ('key', 'name')


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ('key', 'name')


class DocTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocType
        fields = ('key', 'name')


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('key', 'name', 'number', 'phone', 'level', 'company')


class DocumentSerializer(serializers.ModelSerializer):
    upTime = serializers.SerializerMethodField()
    docType = serializers.SlugRelatedField(
        queryset=DocType.objects.all(), label='文档类型', slug_field='name', required=False)

    def get_upTime(self, obj):
        return obj.upTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Document
        fields = ('key', 'name', 'path', 'upTime', 'count', 'up', 'docType')


class DeviceStateSerializer(serializers.ModelSerializer):

    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(), label='设备名称', slug_field='name', required=False)

    class Meta:
        model = DeviceState
        fields = ('key', 'device', 'name', 'time')


class DeviceFaultSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeviceFault
        fields = ('key', 'device', 'isRepair', 'startTime',
                  'endTime', 'operator', 'result')


class DeviceSerializer(serializers.ModelSerializer):
    stateList = serializers.SerializerMethodField()
    joinTime = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    deviceType = serializers.SlugRelatedField(
        queryset=DeviceType.objects.all(), label='设备类型', slug_field='name', required=False)
    process = serializers.SlugRelatedField(
        queryset=Process.objects.all(), label='所在工序', slug_field='name', required=False)

    def get_state(self, obj):
        states = list(DeviceState.objects.filter(
            Q(device=obj)).order_by('time'))
        return states[-1].name if len(states) > 0 else '关机'

    def get_stateList(self, obj):
        states = []
        states = list(map(lambda state: {'name': state.time.strftime('%Y-%m-%d %H:%M:%S'), 'label': state.name,
                                         'description': '%s' % state.name}, obj.states.all()))
        return states

    def get_joinTime(self, obj):
        return obj.joinTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Device
        fields = ('key', 'deviceType', 'process', 'name', 'number', 'joinTime',
                  'exitTime', 'factory', 'facTime', 'facPeo', 'facPho', 'state', 'stateList')


class UserSerializer(serializers.ModelSerializer):

    authority = serializers.SerializerMethodField(read_only=True)
    role = serializers.SlugRelatedField(
        queryset=Role.objects.all(), label='角色', slug_field='name', required=False)
    department = serializers.SlugRelatedField(
        queryset=Organization.objects.all(), label='部门', slug_field='name', required=False)

    def get_authority(self, obj):
        try:
            return obj.role.authority
        except:
            return

    class Meta:
        model = User
        fields = ('key', 'role', 'department', 'authority', 'post',
                  'name', 'gender', 'password', 'phone', 'avatar', 'state')


class OrderSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    status = serializers.SlugRelatedField(
        queryset=OrderStatus.objects.all(), label='订单状态', slug_field='name', required=False)
    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)
    customer = serializers.SlugRelatedField(
        queryset=Customer.objects.all(), label='目标用户', slug_field='name', required=False)
    route = serializers.SlugRelatedField(
        queryset=ProcessRoute.objects.all(), label='选用工艺', slug_field='name', required=False)
    line = serializers.SlugRelatedField(
        queryset=ProductLine.objects.all(), label='选用产线', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Order
        fields = ('key', 'creator', 'number', 'batch', 'scheduling', 'route', 'line', 'customer',
                  'createTime', 'status', 'orderType', 'description')


class ProductLineSerializer(serializers.ModelSerializer):

    workShop = serializers.SlugRelatedField(
        queryset=WorkShop.objects.all(), label='隶属车间', slug_field='name', required=False)
    state = serializers.SlugRelatedField(
        queryset=LineState.objects.all(), label='产线状态', slug_field='name', required=False)
    lineType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='产线类别', slug_field='name', required=False)

    class Meta:
        model = ProductLine
        fields = ('key', 'workShop', 'name', 'state',
                  'number', 'description', 'lineType')


class BottleStateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BottleState
        fields = ('key', 'name')


class LineStateSerializer(serializers.ModelSerializer):

    class Meta:
        model = LineState
        fields = ('key', 'name')


class ProcessRouteSerializer(serializers.ModelSerializer):
    devices = serializers.SerializerMethodField()
    createTime = serializers.SerializerMethodField()
    processes = serializers.StringRelatedField(many=True, read_only=True)
    routeType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='工艺类别', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    def get_devices(self, obj):
        deviceList = Device.objects.all()
        serializer = DeviceSerializer(deviceList, many=True)
        return serializer.data

    class Meta:
        model = ProcessRoute
        fields = ('key', 'name', 'data', 'description', 'routeType',
                  'createTime', 'creator', 'processes', 'devices')


class ProcessSerializer(serializers.ModelSerializer):

    devices = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Process
        fields = ('key', 'route', 'name', 'skip', 'path', 'devices')


class BottleSerializer(serializers.ModelSerializer):

    status = serializers.SlugRelatedField(
        queryset=BottleState.objects.all(), label='瓶子状态', slug_field='name', required=False)

    class Meta:
        model = Bottle
        fields = ('key', 'order', 'number', 'color',
                  'red', 'green', 'blue', 'status')


class WorkOrderSerializer(serializers.ModelSerializer):

    orderNum = serializers.SerializerMethodField()
    createTime = serializers.SerializerMethodField()
    startTime = serializers.SerializerMethodField()
    endTime = serializers.SerializerMethodField()
    events = serializers.StringRelatedField(many=True, read_only=True)
    status = serializers.SlugRelatedField(
        queryset=WorkOrderStatus.objects.all(), label='工单状态', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    def get_startTime(self, obj):
        if obj.startTime:
            return obj.startTime.strftime('%Y-%m-%d %H:%M:%S')
        return ''

    def get_endTime(self, obj):
        if obj.endTime:
            return obj.endTime.strftime('%Y-%m-%d %H:%M:%S')
        return ''

    def get_orderNum(self, obj):
        return obj.order.number

    class Meta:
        model = WorkOrder
        fields = ('key', 'orderNum', 'bottle', 'number', 'createTime',
                  'startTime', 'endTime', 'status', 'description', 'events')


class StoreSerializer(serializers.ModelSerializer):

    workShop = serializers.SlugRelatedField(
        queryset=WorkShop.objects.all(), label='隶属车间', slug_field='name', required=False)
    storeType = serializers.SlugRelatedField(
        queryset=StoreType.objects.all(), label='仓库类型', slug_field='name', required=False)
    productLine = serializers.SlugRelatedField(
        queryset=ProductLine.objects.all(), label='目标产线', slug_field='name', required=False)
    positions = serializers.StringRelatedField(many=True, read_only=True)
    lineType = serializers.SerializerMethodField()
    materials = serializers.SerializerMethodField()

    def get_materials(self, obj):
        return list(set(list(map(lambda obj: obj.name, Material.objects.filter(Q(store__storeType__name='原料库', store__productLine__lineType__name='机加'))))))

    def get_lineType(self, obj):
        try:
            return obj.productLine.lineType.name
        except:
            return ''

    class Meta:
        model = Store
        fields = ('key', 'workShop', 'name', 'dimensions', 'direction', 'productLine', 'lineType',
                  'number', 'storeType', 'positions', 'materials')


class StorePositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = StorePosition
        fields = ('key', 'store', 'number', 'status', 'description', 'content')


class OperateSerializer(serializers.ModelSerializer):

    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        return obj.time.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Operate
        fields = ('key', 'operator', 'name', 'time')


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('key', 'position', 'number', 'rate',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9', 'hole1Content', 'hole2Content', 'hole3Content', 'hole4Content', 'hole5Content', 'hole6Content', 'hole7Content', 'hole8Content', 'hole9Content')


class ProductSerializer(serializers.ModelSerializer):
    stateList = serializers.SerializerMethodField()
    palletStr = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    prodType = serializers.SlugRelatedField(
        queryset=ProductType.objects.all(), label='产品类型', slug_field='name', required=False)

    workOrder = serializers.SlugRelatedField(
        queryset=WorkOrder.objects.all(), label='对应工单', slug_field='number', required=False)

    def get_batch(self, obj):
        return obj.batch.strftime('%Y-%m-%d')

    def get_name(self, obj):
        try:
            return obj.name+'/'+obj.workOrder.bottle
        except:
            return obj.name

    def get_stateList(self, obj):
        states = []
        states = list(map(lambda event: {'name': event.time.strftime('%Y-%m-%d %H:%M:%S'), 'label': event.title,
                                         'description': '%s' % event.title}, Event.objects.filter(Q(workOrder=obj.workOrder))))
        return states

    def get_palletStr(self, obj):
        res = ''
        if obj.pallet:
            if obj.pallet.hole1Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '1')
            if obj.pallet.hole2Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '2')
            if obj.pallet.hole3Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '3')
            if obj.pallet.hole4Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '4')
            if obj.pallet.hole5Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '5')
            if obj.pallet.hole6Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '6')
            if obj.pallet.hole7Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '7')
            if obj.pallet.hole8Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '8')
            if obj.pallet.hole9Content == obj.workOrder.bottle:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '9')
        else:
            try:
                pos = StorePosition.objects.get(content=obj.name)
                res = '%s-%s号位' % (pos.store.name, pos.number.split('-')[0])
            except:
                res = ''
        return res

    class Meta:
        model = Product
        fields = ('key', 'prodType', 'workOrder', 'result', 'pallet',
                  'name', 'number',  'batch', 'palletStr', 'reason',  'stateList')


class ProductTypeSerializer(serializers.ModelSerializer):

    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)

    class Meta:
        model = ProductType
        fields = ('key', 'name', 'number', 'path', 'orderType', 'errorRange')


class DataViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataView
        fields = ('key', 'mwContent', 'gzContent')


class ProductStandardSerializer(serializers.ModelSerializer):
    batch = serializers.SerializerMethodField()
    product = serializers.SlugRelatedField(
        queryset=Product.objects.all(), label='产品名称', slug_field='name', required=False)

    def get_batch(self, obj):
        try:
            return obj.product.batch.strftime('%Y-%m-%d')
        except:
            return ''

    class Meta:
        model = ProductStandard
        fields = ('key', 'product', 'name', 'batch',
                  'expectValue', 'realValue', 'result')


class EventSerializer(serializers.ModelSerializer):

    bottle = serializers.SerializerMethodField()

    def get_bottle(self, obj):
        return obj.workOrder.bottle

    class Meta:
        model = Event
        fields = ('key', 'title', 'source', 'bottle', 'time', 'workOrder')


class MaterialSerializer(serializers.ModelSerializer):

    store = serializers.SlugRelatedField(
        queryset=Store.objects.all(), label='所在仓库', slug_field='name', required=False)

    class Meta:
        model = Material
        fields = ('key', 'name', 'size',
                  'unit', 'mateType', 'store')


class ToolSerializer(serializers.ModelSerializer):

    store = serializers.SlugRelatedField(
        queryset=Store.objects.all(), label='所在仓库', slug_field='name', required=False)

    class Meta:
        model = Tool
        fields = ('key', 'name', 'size',
                  'unit', 'toolType', 'store')


class BOMSerializer(serializers.ModelSerializer):

    createTime = serializers.SerializerMethodField()
    product = serializers.SlugRelatedField(
        queryset=ProductType.objects.all(), label='对应产品', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = BOM
        fields = ('key', 'product', 'name', 'content', 'creator', 'createTime')
