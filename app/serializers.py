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
    class Meta:
        model = Department
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
    number = serializers.SerializerMethodField()
    createTime = serializers.SerializerMethodField()
    status = serializers.SlugRelatedField(
        queryset=OrderStatus.objects.all(), label='订单状态', slug_field='name', required=False)
    orderType = serializers.SlugRelatedField(
        queryset=OrderType.objects.all(), label='订单类型', slug_field='name', required=False)

    def get_number(self, obj):
        return int(time.mktime(obj.number.timetuple())*1000)

    def get_createTime(self, obj):
        return str(obj.createTime)

    class Meta:
        model = Order
        fields = ('key', 'creator', 'number',
                  'createTime', 'status', 'orderType', 'description')


class ProcessLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessLine
        fields = ('key', 'workShop', 'name',
                  'number', 'description')


class ProcessRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessRoute
        fields = ('key', 'name', 'description',
                  'status', 'createTime', 'creator')


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('key', 'route', 'name',
                  'number', 'description', 'status')


class WorkOrderSerializer(serializers.ModelSerializer):

    orderNum = serializers.SerializerMethodField()
    status = serializers.SlugRelatedField(
        queryset=WorkOrderStatus.objects.all(), label='工单状态', slug_field='name', required=False)

    def get_orderNum(self, obj):
        return obj.order.number

    class Meta:
        model = WorkOrder
        fields = ('key', 'orderNum', 'route', 'number', 'createTime',
                  'startTime', 'endTime', 'status', 'description')


class BOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOM
        fields = ('key', 'user', 'name',
                  'number', 'description', 'bomType', 'createTime')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('key', 'workShop', 'name',
                  'number', 'storeType')


class StroePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StroePosition
        fields = ('key', 'store', 'number')


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('key', 'store', 'position', 'number',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9')


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ('key', 'bom', 'user',
                  'store', 'position', 'workOrder', 'name', 'number', 'description', 'mateType', 'operate', 'operateTime')


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
    class Meta:
        model = Event
        fields = ('key', 'title', 'source', 'time')
