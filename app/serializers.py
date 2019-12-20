from app.models import *
from rest_framework import serializers


class WorkShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShop
        fields = ('id', 'name', 'number',
                  'descriptions', 'createTime', 'status')


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')


class RoleSerializer(serializers.ModelSerializer):
    key = serializers.SerializerMethodField()

    def get_key(self, obj):
        return str(obj.id)

    class Meta:
        model = Role
        fields = ('id', 'key', 'name', 'authority')


class UserSerializer(serializers.ModelSerializer):

    key = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    authority = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    gender = serializers.ChoiceField(
        choices=User.USER_GENDER, source='get_gender_display', read_only=True)

    def get_key(self, obj):
        return str(obj.id)

    def get_role(self, obj):
        return obj.role.name if obj.role else ''

    def get_authority(self, obj):
        return obj.role.authority if obj.role else ''

    def get_department(self, obj):
        return obj.department.name if obj.department else ''

    class Meta:
        model = User
        fields = ('id', 'key', 'department', 'authority', 'role',
                  'name', 'gender', 'password', 'phone', 'company')


class OrderSerializer(serializers.ModelSerializer):

    key = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    orderType = serializers.ChoiceField(
        choices=Order.ORDER_STATUS, source='get_orderType_display', read_only=True)
    status = serializers.ChoiceField(
        choices=Order.ORDER_STATUS, source='get_status_display', read_only=True)

    def get_key(self, obj):
        return str(obj.id)

    def get_user(self, obj):
        return str(obj.user.name)

    class Meta:
        model = Order
        fields = ('id', 'key', 'user', 'number',
                  'createTime', 'status', 'orderType', 'description')


class ProcessLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessLine
        fields = ('id', 'workShop', 'name',
                  'number', 'description')


class ProcessRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessRoute
        fields = ('id', 'name', 'description',
                  'status', 'createTime', 'creator')


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('id', 'route', 'name',
                  'number', 'description', 'status')


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = ('id', 'order', 'route',
                  'number', 'createTime', 'startTime', 'endTime', 'status', 'description')


class BOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOM
        fields = ('id', 'user', 'name',
                  'number', 'description', 'bomType', 'createTime')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'workShop', 'name',
                  'number', 'storeType')


class StroePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StroePosition
        fields = ('id', 'store', 'number')


class PalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pallet
        fields = ('id', 'store', 'position', 'number',
                  'hole1', 'hole2', 'hole3', 'hole4', 'hole5', 'hole6', 'hole7', 'hole8', 'hole9')


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ('id', 'bom', 'user',
                  'store', 'position', 'workOrder', 'name', 'number', 'description', 'mateType', 'operate', 'operateTime')


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'user', 'store',
                  'position', 'name', 'number', 'description', 'prodType', 'batch', 'pic', 'operate', 'operateTime')


class ProductStandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStandard
        fields = ('id', 'product', 'name',
                  'expectValue', 'realValue', 'result')


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'title', 'source', 'time')
