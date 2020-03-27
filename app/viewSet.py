import json
from app.models import *
from app.serializers import *
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.


class WorkShopViewSet(viewsets.ModelViewSet):
    queryset = WorkShop.objects.all().order_by('-createTime')
    serializer_class = WorkShopSerializer


class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all().order_by('-createTime')
    serializer_class = BOMSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class OrgaLevelViewSet(viewsets.ModelViewSet):
    queryset = OrgaLevel.objects.all()
    serializer_class = OrgaLevelSerializer


class OrderTypeViewSet(viewsets.ModelViewSet):
    queryset = OrderType.objects.all()
    serializer_class = OrderTypeSerializer


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


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-key')
    serializer_class = OrderSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        route = ProcessRoute.objects.get(Q(name__icontains=data['orderType']))
        line = ProductLine.objects.get(Q(name__icontains=data['orderType']))
        data['route'] = route
        data['line'] = line
        serializer = self.get_serializer(
            instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ProductLineViewSet(viewsets.ModelViewSet):
    queryset = ProductLine.objects.all().order_by('-key')
    serializer_class = ProductLineSerializer


class ProcessRouteViewSet(viewsets.ModelViewSet):
    queryset = ProcessRoute.objects.all().order_by('-key')
    serializer_class = ProcessRouteSerializer


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


class StoreTypeViewSet(viewsets.ModelViewSet):
    queryset = StoreType.objects.all()
    serializer_class = StoreTypeSerializer


class StorePositionViewSet(viewsets.ModelViewSet):
    queryset = StorePosition.objects.all()
    serializer_class = StorePositionSerializer


class OperateViewSet(viewsets.ModelViewSet):
    queryset = Operate.objects.all().order_by('-time')
    serializer_class = OperateSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('-key')
    serializer_class = DeviceSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['docType']


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


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer


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
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer


class ProductStandardViewSet(viewsets.ModelViewSet):
    queryset = ProductStandard.objects.all().order_by('-key')
    serializer_class = ProductStandardSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        product = Product.objects.get(
            Q(workOrder__number=request.data['product'].split('/')[1]))
        product.result = '1' if str(request.data['result']) == '1' else '2'
        product.reason = '%s未达到%s的预期结果' % (
            request.data['name'], request.data['expectValue'])
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
