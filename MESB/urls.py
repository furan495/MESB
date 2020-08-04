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
router.register(r'api/tools', viewSet.ToolViewSet)
router.register(r'api/orders', viewSet.OrderViewSet)
router.register(r'api/stores', viewSet.StoreViewSet)
router.register(r'api/events', viewSet.EventViewSet)
router.register(r'api/columns', viewSet.ColumnViewSet)
router.register(r'api/devices', viewSet.DeviceViewSet)
router.register(r'api/pallets', viewSet.PalletViewSet)
router.register(r'api/operates', viewSet.OperateViewSet)
router.register(r'api/products', viewSet.ProductViewSet)
router.register(r'api/docTypes', viewSet.DocTypeViewSet)
router.register(r'api/processes', viewSet.ProcessViewSet)
router.register(r'api/materials', viewSet.MaterialViewSet)
router.register(r'api/workShops', viewSet.WorkShopViewSet)
router.register(r'api/customers', viewSet.CustomerViewSet)
router.register(r'api/documents', viewSet.DocumentViewSet)
router.register(r'api/storeTypes', viewSet.StoreTypeViewSet)
router.register(r'api/workOrders', viewSet.WorkOrderViewSet)
router.register(r'api/orderTypes', viewSet.OrderTypeViewSet)
router.register(r'api/bomContents', viewSet.BOMContentViewSet)
router.register(r'api/deviceTypes', viewSet.DeviceTypeViewSet)
router.register(r'api/deviceBases', viewSet.DeviceBaseViewSet)
router.register(r'api/palletHoles', viewSet.PalletHoleViewSet)
router.register(r'api/deviceStates', viewSet.DeviceStateViewSet)
router.register(r'api/productLines', viewSet.ProductLineViewSet)
router.register(r'api/productTypes', viewSet.ProductTypeViewSet)
router.register(r'api/productInfos', viewSet.ProductInfoViewSet)
router.register(r'api/commonStatus', viewSet.CommonStatusViewSet)
router.register(r'api/organizations', viewSet.OrganizationViewSet)
router.register(r'api/processRoutes', viewSet.ProcessRouteViewSet)
router.register(r'api/processParams', viewSet.ProcessParamsViewSet)
router.register(r'api/storePositions', viewSet.StorePositionViewSet)
router.register(r'api/productStandards', viewSet.ProductStandardViewSet)

# API URL现在由路由器自动确定。
# 另外，我们还要包含可浏览的API的登录URL。
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api/wincc/',  views.wincc),
    url(r'^api/selects/',  views.selects),
    url(r'^api/queryCharts/',  views.queryCharts),
    url(r'^upload/(?P<path>.*)$', serve,{'document_root': BASE_DIR+'/upload'}),
]
