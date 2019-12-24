import os
from app import viewSet, views
from django.contrib import admin
from django.views.static import serve
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建路由器并注册我们的视图。
router = DefaultRouter()
router.register(r'api/boms', viewSet.BOMViewSet)
router.register(r'api/roles', viewSet.RoleViewSet)
router.register(r'api/users', viewSet.UserViewSet)
router.register(r'api/orders', viewSet.OrderViewSet)
router.register(r'api/stores', viewSet.StoreViewSet)
router.register(r'api/events', viewSet.EventViewSet)
router.register(r'api/pallets', viewSet.PalletViewSet)
router.register(r'api/products', viewSet.ProductViewSet)
router.register(r'api/processes', viewSet.ProcessViewSet)
router.register(r'api/workShops', viewSet.WorkShopViewSet)
router.register(r'api/materials', viewSet.MaterialViewSet)
router.register(r'api/workOrders', viewSet.WorkOrderViewSet)
router.register(r'api/orderTypes', viewSet.OrderTypeViewSet)
router.register(r'api/departments', viewSet.DepartmentViewSet)
router.register(r'api/processLines', viewSet.ProcessLineViewSet)
router.register(r'api/orderStatuses', viewSet.OrderStatusViewSet)
router.register(r'api/processRoutes', viewSet.ProcessRouteViewSet)
router.register(r'api/stroePositions', viewSet.StroePositionViewSet)
router.register(r'api/productStandards', viewSet.ProductStandardViewSet)
router.register(r'api/workOrderStatuses', viewSet.WorkOrderStatusViewSet)

# API URL现在由路由器自动确定。
# 另外，我们还要包含可浏览的API的登录URL。
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^api/orderSplit/',  views.orderSplit),
    url(r'^api/querySelect/',  views.querySelect),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
