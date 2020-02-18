import time
from app.models import *
from rest_framework import serializers


class WorkShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShop
        fields = ('key', 'name', 'number',
                  'descriptions', 'createTime')


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


class DocumentSerializer(serializers.ModelSerializer):
    upTime = serializers.SerializerMethodField()

    def get_upTime(self, obj):
        return obj.upTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Document
        fields = ('key', 'name', 'path', 'upTime', 'count', 'up')


class DeviceStateSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(), label='设备名称', slug_field='name', required=False)

    class Meta:
        model = DeviceState
        fields = ('key', 'device', 'isOpen', 'openTime', 'closeTime', 'isWork', 'workStart', 'workEnd', 'isFault',
                  'faultTime', 'faultLevel', 'faultReason', 'isRepair', 'repairStart', 'repairEnd', 'repairResult')


class DeviceSerializer(serializers.ModelSerializer):
    joinTime = serializers.SerializerMethodField()
    deviceType = serializers.SlugRelatedField(
        queryset=DeviceType.objects.all(), label='设备类型', slug_field='name', required=False)
    process = serializers.SlugRelatedField(
        queryset=Process.objects.all(), label='所在工序', slug_field='name', required=False)

    def get_joinTime(self, obj):
        return obj.joinTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Device
        fields = ('key', 'deviceType', 'process', 'name', 'number', 'joinTime',
                  'exitTime', 'factory', 'facTime', 'facPeo', 'facPho')


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
        fields = ('key', 'role', 'department', 'authority',
                  'name', 'gender', 'password', 'phone', 'company')


class OrderSerializer(serializers.ModelSerializer):
    createTime = serializers.SerializerMethodField()
    status = serializers.SlugRelatedField(
        queryset=OrderStatus.objects.all(), label='订单状态', slug_field='name', required=False)
    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Order
        fields = ('key', 'creator', 'number', 'batch', 'scheduling',
                  'createTime', 'status', 'orderType', 'description')


class ProductLineSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductLine
        fields = ('key', 'workShop', 'name',
                  'number', 'description')


class BottleStateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BottleState
        fields = ('key', 'name')


class WorkPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPosition
        fields = ('key', 'productLine', 'name')


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
        fields = ('key', 'operator', 'name', 'time', 'pallet',
                  'device', 'order', 'processRuote', 'store', 'document')


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('key', 'position', 'number', 'rate',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9', 'hole1Content', 'hole2Content', 'hole3Content', 'hole4Content', 'hole5Content', 'hole6Content', 'hole7Content', 'hole8Content', 'hole9Content')


class ProductSerializer(serializers.ModelSerializer):
    palletStr = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    prodType = serializers.SlugRelatedField(
        queryset=ProductType.objects.all(), label='产品类型', slug_field='name', required=False)

    workOrder = serializers.SlugRelatedField(
        queryset=WorkOrder.objects.all(), label='对应工单', slug_field='number', required=False)

    def get_batch(self, obj):
        return obj.batch.strftime('%Y-%m-%d %H:%M:%S')

    def get_palletStr(self, obj):
        res = ''
        if obj.pallet:
            if obj.pallet.hole1Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '1')
            elif obj.pallet.hole2Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '2')
            elif obj.pallet.hole3Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '3')
            elif obj.pallet.hole4Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '4')
            elif obj.pallet.hole5Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '5')
            elif obj.pallet.hole6Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '6')
            elif obj.pallet.hole7Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '7')
            elif obj.pallet.hole8Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '8')
            elif obj.pallet.hole9Content == obj.name:
                res = '%s-%s号位-%s号孔' % (obj.pallet.position.store.name,
                                        obj.pallet.position.number, '9')
            else:
                pass
        return res

    class Meta:
        model = Product
        fields = ('key', 'pallet', 'prodType', 'workOrder',
                  'name', 'number', 'description',  'batch', 'palletStr', 'reason')


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ('key', 'name')


class ProductStandardSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    product = serializers.SlugRelatedField(
        queryset=Product.objects.all(), label='产品名称', slug_field='name', required=False)

    def get_description(self, obj):
        description = ''
        if obj.product:
            description = obj.product.description
        return description

    class Meta:
        model = ProductStandard
        fields = ('key', 'product', 'name',
                  'expectValue', 'realValue', 'result', 'description')


class EventSerializer(serializers.ModelSerializer):

    bottle = serializers.SerializerMethodField()

    def get_bottle(self, obj):
        return obj.workOrder.bottle

    class Meta:
        model = Event
        fields = ('key', 'title', 'source', 'bottle', 'time', 'workOrder')
