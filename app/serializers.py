import time
from app.models import *
from django.db.models import Q
from rest_framework import serializers


class WorkShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShop
        fields = ('key', 'name', 'number',
                  'descriptions', 'createTime', 'status')


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
        fields = ('key', 'creator', 'number', 'route', 'batch', 'scheduling',
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
    createTime = serializers.SerializerMethodField()
    processes = serializers.StringRelatedField(many=True, read_only=True)

    def get_createTime(self, obj):
        return obj.createTime.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ProcessRoute
        fields = ('key', 'name', 'data', 'description',
                  'createTime', 'creator', 'processes')


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('key', 'route', 'name')


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


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('key', 'position', 'number','rate',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9', 'hole1Content', 'hole2Content', 'hole3Content', 'hole4Content', 'hole5Content', 'hole6Content', 'hole7Content', 'hole8Content', 'hole9Content')


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('key', 'user', 'store',
                  'position', 'name', 'number', 'description', 'prodType', 'batch', 'pic', 'operate', 'operateTime')


class ProductStandardSerializer(serializers.ModelSerializer):
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
