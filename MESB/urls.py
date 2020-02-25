import os
from app import viewSet, views
from django.contrib import admin
from django.views.static import serve
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建路由器并注册我们的视图。
router = DefaultRouter()
#router.register(r'api/boms', viewSet.BOMViewSet)
router.register(r'api/roles', viewSet.RoleViewSet)
router.register(r'api/users', viewSet.UserViewSet)
router.register(r'api/orders', viewSet.OrderViewSet)
router.register(r'api/stores', viewSet.StoreViewSet)
router.register(r'api/events', viewSet.EventViewSet)
router.register(r'api/devices', viewSet.DeviceViewSet)
router.register(r'api/bottles', viewSet.BottleViewSet)
router.register(r'api/pallets', viewSet.PalletViewSet)
router.register(r'api/operates', viewSet.OperateViewSet)
router.register(r'api/products', viewSet.ProductViewSet)
router.register(r'api/processes', viewSet.ProcessViewSet)
router.register(r'api/materials', viewSet.MaterialViewSet)
router.register(r'api/workShops', viewSet.WorkShopViewSet)
router.register(r'api/documents', viewSet.DocumentViewSet)
router.register(r'api/lineStates', viewSet.LineStateViewSet)
router.register(r'api/storeTypes', viewSet.StoreTypeViewSet)
router.register(r'api/workOrders', viewSet.WorkOrderViewSet)
router.register(r'api/orderTypes', viewSet.OrderTypeViewSet)
router.register(r'api/deviceTypes', viewSet.DeviceTypeViewSet)
router.register(r'api/departments', viewSet.DepartmentViewSet)
router.register(r'api/deviceStates', viewSet.DeviceStateViewSet)
router.register(r'api/deviceFaults', viewSet.DeviceFaultViewSet)
router.register(r'api/productLines', viewSet.ProductLineViewSet)
router.register(r'api/bottleStates', viewSet.BottleStateViewSet)
router.register(r'api/productTypes', viewSet.ProductTypeViewSet)
router.register(r'api/workPostions', viewSet.WorkPositionViewSet)
router.register(r'api/orderStatuses', viewSet.OrderStatusViewSet)
router.register(r'api/processRoutes', viewSet.ProcessRouteViewSet)
router.register(r'api/materialGroups', viewSet.MaterialGroupViewSet)
router.register(r'api/stroePositions', viewSet.StroePositionViewSet)
router.register(r'api/productStandards', viewSet.ProductStandardViewSet)
router.register(r'api/workOrderStatuses', viewSet.WorkOrderStatusViewSet)

# API URL现在由路由器自动确定。
# 另外，我们还要包含可浏览的API的登录URL。
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^api/wincc/',  views.wincc),
    url(r'^api/upload/',  views.upload),
    url(r'^api/uploadPic/',  views.uploadPic),
    url(r'^api/updatePWD/',  views.updatePWD),
    url(r'^api/addBottle/',  views.addBottle),
    url(r'^api/loginCheck/',  views.loginCheck),
    url(r'^api/orderSplit/',  views.orderSplit),
    url(r'^api/queryPallet/',  views.queryPallet),
    url(r'^api/updateCount/',  views.updateCount),
    url(r'^api/createStore/',  views.createStore),
    url(r'^api/querySelect/',  views.querySelect),
    url(r'^api/uploadAvatar/',  views.uploadAvatar),
    url(r'^api/updateDevice/',  views.updateDevice),
    url(r'^api/storeOperate/',  views.storeOperate),
    url(r'^api/queryOperateChart/',  views.queryOperateChart),
    url(r'^upload/(?P<path>.*)$', serve,
        {'document_root': BASE_DIR+'/upload'}),
    url(r'^api/updateProcessByRoute/',  views.updateProcessByRoute),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
