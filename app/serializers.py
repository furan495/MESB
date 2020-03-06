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
        fields = ('key', 'name', 'level', 'parent')


class OrgaLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrgaLevel
        fields = ('key', 'name')


class DepartmentSerializer(serializers.ModelSerializer):

    members = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ('key', 'name', 'members')


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
        queryset=Department.objects.all(), label='部门', slug_field='name', required=False)

    def get_authority(self, obj):
        try:
            return obj.role.authority
        except:
            return

    class Meta:
        model = User
        fields = ('key', 'role', 'department', 'authority', 'post',
                  'name', 'gender', 'password', 'phone', 'avatar')


class OrderSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    status = serializers.SlugRelatedField(
        queryset=OrderStatus.objects.all(), label='订单状态', slug_field='name', required=False)
    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)
    route = serializers.SlugRelatedField(
        queryset=ProcessRoute.objects.all(), label='选用工艺', slug_field='name', required=False)
    line = serializers.SlugRelatedField(
        queryset=ProductLine.objects.all(), label='选用产线', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Order
        fields = ('key', 'creator', 'number', 'batch', 'scheduling', 'route', 'line',
                  'createTime', 'status', 'orderType', 'description')


class ProductLineSerializer(serializers.ModelSerializer):

    workShop = serializers.SlugRelatedField(
        queryset=WorkShop.objects.all(), label='隶属车间', slug_field='name', required=False)
    state = serializers.SlugRelatedField(
        queryset=LineState.objects.all(), label='产线状态', slug_field='name', required=False)

    class Meta:
        model = ProductLine
        fields = ('key', 'workShop', 'name', 'state',
                  'number', 'description')


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

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    def get_devices(self, obj):
        deviceList = Device.objects.all()
        serializer = DeviceSerializer(deviceList, many=True)
        return serializer.data

    class Meta:
        model = ProcessRoute
        fields = ('key', 'name', 'data', 'description',
                  'createTime', 'creator', 'processes', 'devices')


class ProcessSerializer(serializers.ModelSerializer):

    devices = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Process
        fields = ('key', 'route', 'name', 'skip', 'path', 'devices')


class BottleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bottle
        fields = ('key', 'order', 'number', 'color', 'red', 'green', 'blue')


class WorkOrderSerializer(serializers.ModelSerializer):

    orderNum = serializers.SerializerMethodField()
    createTime = serializers.SerializerMethodField()
    events = serializers.StringRelatedField(many=True, read_only=True)
    status = serializers.SlugRelatedField(
        queryset=WorkOrderStatus.objects.all(), label='工单状态', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

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
    positions = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Store
        fields = ('key', 'workShop', 'name', 'dimensions',
                  'number', 'storeType', 'positions')


class StroePositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = StroePosition
        fields = ('key', 'store', 'number', 'status')


class OperateSerializer(serializers.ModelSerializer):

    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        return obj.time.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Operate
        fields = ('key', 'operator', 'name', 'time', 'target')


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('key', 'position', 'number', 'rate',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9', 'hole1Content', 'hole2Content', 'hole3Content', 'hole4Content', 'hole5Content', 'hole6Content', 'hole7Content', 'hole8Content', 'hole9Content')


class ProductSerializer(serializers.ModelSerializer):
    stateList = serializers.SerializerMethodField()
    palletStr = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    prodType = serializers.SlugRelatedField(
        queryset=ProductType.objects.all(), label='产品类型', slug_field='name', required=False)

    workOrder = serializers.SlugRelatedField(
        queryset=WorkOrder.objects.all(), label='对应工单', slug_field='number', required=False)

    def get_batch(self, obj):
        return obj.batch.strftime('%Y-%m-%d')

    def get_stateList(self, obj):
        states = []
        states = list(map(lambda event: {'name': event.time.strftime('%Y-%m-%d %H:%M:%S'), 'label': event.title,
                                         'description': '%s' % event.title}, Event.objects.filter(Q(workOrder=obj.workOrder))))
        return states

    def get_palletStr(self, obj):
        res = ''
        if obj.pallet:
            if obj.pallet.hole1Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '1')
            elif obj.pallet.hole2Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '2')
            elif obj.pallet.hole3Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '3')
            elif obj.pallet.hole4Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '4')
            elif obj.pallet.hole5Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '5')
            elif obj.pallet.hole6Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '6')
            elif obj.pallet.hole7Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '7')
            elif obj.pallet.hole8Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '8')
            elif obj.pallet.hole9Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number.split('-')[0], '9')
            else:
                pass
        return res

    class Meta:
        model = Product
        fields = ('key', 'prodType', 'workOrder', 'result',
                  'name', 'number',  'batch', 'palletStr', 'reason',  'stateList')


class ProductTypeSerializer(serializers.ModelSerializer):

    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)

    class Meta:
        model = ProductType
        fields = ('key', 'name', 'number', 'path', 'orderType', 'errorRange')


class ProductStandardSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(
        queryset=Product.objects.all(), label='产品名称', slug_field='name', required=False)

    class Meta:
        model = ProductStandard
        fields = ('key', 'product', 'name',
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
