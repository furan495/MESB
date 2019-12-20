from app.models import *
from app.serializers import *
from rest_framework import viewsets
from rest_framework.response import Response

# Create your views here.


class WorkShopViewSet(viewsets.ModelViewSet):
    queryset = WorkShop.objects.all()
    serializer_class = WorkShopSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class ProcessLineViewSet(viewsets.ModelViewSet):
    queryset = ProcessLine.objects.all()
    serializer_class = ProcessLineSerializer


class ProcessRouteViewSet(viewsets.ModelViewSet):
    queryset = ProcessRoute.objects.all()
    serializer_class = ProcessRouteSerializer


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer


class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class StroePositionViewSet(viewsets.ModelViewSet):
    queryset = StroePosition.objects.all()
    serializer_class = StroePositionSerializer


class PalletViewSet(viewsets.ModelViewSet):
    queryset = Pallet.objects.all()
    serializer_class = PalletSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductStandardViewSet(viewsets.ModelViewSet):
    queryset = ProductStandard.objects.all()
    serializer_class = ProductStandardSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
