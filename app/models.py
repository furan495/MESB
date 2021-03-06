import time
from django.db import models
from django.db.models import Q

# Create your models here.


class DocType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=10, verbose_name='文档类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '文档类型'


class CommonStatus(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=10, verbose_name='状态名称', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '状态'


class Document(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    docType = models.ForeignKey(
        DocType, related_name='documents', on_delete=models.CASCADE, verbose_name='文档类型', blank=True, null=True)
    name = models.CharField(
        max_length=100, verbose_name='文档名称', blank=True, null=True)
    path = models.CharField(
        max_length=200, verbose_name='文档路径', blank=True, null=True)
    up = models.CharField(verbose_name='上传者', max_length=20)
    upTime = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    count = models.IntegerField(verbose_name='浏览次数', default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '文档'


class WorkShop(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='车间名称', unique=True, blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='车间编号', unique=True, blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='车间描述', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '车间'


class Organization(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='组织名称', blank=True, null=True)
    parent = models.CharField(
        max_length=20, verbose_name='上级组织', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '组织'


class Role(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=10, verbose_name='角色名', blank=True, null=True)
    authority = models.CharField(
        max_length=500, verbose_name='权限', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '角色'


class User(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='姓名', unique=True, blank=True, null=True)
    role = models.ForeignKey(Role, related_name='users',
                             on_delete=models.CASCADE, verbose_name='角色', blank=True, null=True)
    department = models.ForeignKey(
        Organization, related_name='members', on_delete=models.CASCADE, verbose_name='部门', blank=True, null=True)
    password = models.CharField(
        max_length=20, verbose_name='密码', blank=True, null=True, default='123456')
    gender = models.CharField(
        max_length=2, verbose_name='性别', blank=True, null=True)
    phone = models.CharField(
        max_length=20, verbose_name='账号', unique=True, blank=True, null=True)
    post = models.CharField(
        max_length=20, verbose_name='职位', blank=True, null=True)
    status = models.CharField(
        max_length=20, verbose_name='状态', blank=True, null=True, default='离线')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '用户'


class OrderType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='订单类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '订单类型'


class ProcessRoute(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工艺名称', unique=True, blank=True, null=True)
    routeType = models.ForeignKey(
        OrderType, related_name='routes', on_delete=models.CASCADE, verbose_name='工艺类别', blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='工艺描述', blank=True, null=True)
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)
    data = models.CharField(
        max_length=4000, verbose_name='工艺内容', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工艺路线'


class ProductLine(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='产线名称', unique=True, blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='产线编号', unique=True, blank=True, null=True)
    lineType = models.ForeignKey(
        OrderType, related_name='lines', on_delete=models.CASCADE, verbose_name='产线类别', blank=True, null=True)
    workShop = models.ForeignKey(WorkShop, related_name='productLines',
                                 on_delete=models.CASCADE, verbose_name='隶属车间', blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='产线描述', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产线'


class Customer(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='客户名', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='客户编号', blank=True, null=True)
    phone = models.CharField(
        max_length=20, verbose_name='联系电话', blank=True, null=True)
    level = models.IntegerField(verbose_name='客户等级', blank=True, null=True)
    company = models.CharField(
        max_length=20, verbose_name='公司名称', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '客户'


class Order(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    orderType = models.ForeignKey(OrderType, related_name='types',
                                  on_delete=models.CASCADE, verbose_name='订单类型', blank=True, null=True)
    route = models.ForeignKey(ProcessRoute, related_name='orders',
                              on_delete=models.CASCADE, verbose_name='选用工艺', blank=True, null=True)
    line = models.ForeignKey(ProductLine, related_name='orders',
                             on_delete=models.CASCADE, verbose_name='选用产线', blank=True, null=True)
    customer = models.ForeignKey(Customer, related_name='orders',
                                 on_delete=models.CASCADE, verbose_name='目标客户', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='订单编号', default=str(time.time()*1000)[:10])
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True,
                                      verbose_name='创建时间')
    status = models.ForeignKey(CommonStatus, related_name='orders',
                               on_delete=models.CASCADE, verbose_name='订单状态', default='1', blank=True, null=True)
    scheduling = models.CharField(max_length=50,
                                  verbose_name='排产时间', blank=True, null=True)
    content = models.CharField(
        max_length=200, verbose_name='订单描述', blank=True, null=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = '订单'


class Process(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工序名称', blank=True, null=True)
    route = models.ForeignKey(ProcessRoute, related_name='processes',
                              on_delete=models.CASCADE, verbose_name='隶属工艺', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='工序编号', blank=True, null=True)
    path = models.CharField(
        max_length=200, verbose_name='工序图片', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工序'


class ProcessParams(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    process = models.ForeignKey(Process, related_name='params',
                                on_delete=models.CASCADE, verbose_name='对应工序')
    name = models.CharField(max_length=20, verbose_name='参数名称')
    tagName = models.CharField(max_length=20, verbose_name='参数标签')
    value = models.FloatField(verbose_name='参数值')
    unit = models.CharField(
        max_length=20, verbose_name='参数单位', blank=True, null=True)
    topLimit = models.FloatField(verbose_name='参数上限')
    lowLimit = models.FloatField(verbose_name='参数下限')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工艺参数'


class DeviceType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='设备类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '设备类型'


class Device(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    process = models.ForeignKey(Process, related_name='devices',
                                on_delete=models.CASCADE, verbose_name='所在工序', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='设备名称', blank=True, null=True)
    deviceType = models.ForeignKey(DeviceType, related_name='devices',
                                   on_delete=models.CASCADE, verbose_name='设备类型', blank=True, null=True)
    typeNumber = models.CharField(
        max_length=20, verbose_name='设备型号', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='设备IP', unique=True, blank=True, null=True)
    factory = models.CharField(
        max_length=20, verbose_name='设备厂家', blank=True, null=True)

    def __str__(self):
        return self.name+'/'+self.typeNumber

    class Meta:
        verbose_name = '设备'


class DeviceBase(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    device = models.ForeignKey(Device, related_name='properties',
                               on_delete=models.CASCADE, verbose_name='对应设备')
    name = models.CharField(
        max_length=20, verbose_name='属性名称', blank=True, null=True)
    value = models.CharField(
        max_length=20, verbose_name='属性值', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '设备属性'


class DeviceState(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    device = models.ForeignKey(Device, related_name='states',
                               on_delete=models.CASCADE, verbose_name='对应设备')
    name = models.CharField(
        max_length=20, verbose_name='状态名称', blank=True, null=True)
    value = models.CharField(
        max_length=200, verbose_name='状态值', blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')

    def __str__(self):
        return self.name+'/'+str(self.time)

    class Meta:
        verbose_name = '设备状态'


class StoreType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='仓库类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '仓库类型'


class Store(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='仓库名称', unique=True, blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='仓库编号', unique=True, blank=True, null=True)
    storeType = models.ForeignKey(StoreType, related_name='stores',
                                  on_delete=models.CASCADE, verbose_name='仓库类型', blank=True, null=True)
    workShop = models.ForeignKey(WorkShop, related_name='stores',
                                 on_delete=models.CASCADE, verbose_name='隶属车间', blank=True, null=True)
    productLine = models.ForeignKey(ProductLine, related_name='stores',
                                    on_delete=models.CASCADE, verbose_name='目标产线', blank=True, null=True)
    rows = models.IntegerField(verbose_name='仓库行数', blank=True, null=True)
    columns = models.IntegerField(verbose_name='仓库列数', blank=True, null=True)
    origin = models.CharField(
        max_length=20, verbose_name='原点位置', blank=True, null=True)
    direction = models.CharField(
        max_length=20, verbose_name='仓库排向', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '仓库'


class StorePosition(models.Model):
    POSITION_STATUS = (
        ('1', '有料'),
        ('2', '无料'),
    )
    key = models.AutoField(primary_key=True, verbose_name='主键')
    store = models.ForeignKey(Store, related_name='positions',
                              on_delete=models.CASCADE, verbose_name='隶属仓库')
    status = models.CharField(
        max_length=2, verbose_name='仓位状态', choices=POSITION_STATUS, blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='仓位编号')
    description = models.CharField(
        max_length=20, verbose_name='仓位描述', blank=True, null=True, default='')
    content = models.CharField(
        max_length=200, verbose_name='存放物料', blank=True, null=True, default='')

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '仓位'


class Pallet(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    position = models.ForeignKey(StorePosition, related_name='positions',
                                 on_delete=models.CASCADE, verbose_name='隶属仓位', blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='托盘编号')
    rate = models.FloatField(verbose_name='利用率', default=0.0)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '托盘'


class PalletHole(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    pallet = models.ForeignKey(Pallet, related_name='holes',
                               on_delete=models.CASCADE, verbose_name='隶属托盘')
    number = models.CharField(max_length=20, verbose_name='孔号')
    status = models.BooleanField(verbose_name='孔位状态', default=False)
    content = models.CharField(
        max_length=20, verbose_name='存放物', blank=True, null=True)

    def save(self):
        super(PalletHole, self).save()
        pallet = self.pallet
        pallet.rate = round(PalletHole.objects.filter(
            Q(pallet=pallet, status=True)).count()/9, 2)
        pallet.save()

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '托盘孔'


class Operate(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='操作名称')
    operator = models.CharField(
        max_length=20, verbose_name='操作人')
    time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '操作'


class ProductType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='产品名称', unique=True, blank=True, null=True)
    orderType = models.ForeignKey(OrderType, related_name='products',
                                  on_delete=models.CASCADE, verbose_name='产品类型', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='产品编号', unique=True, blank=True, null=True)
    errorRange = models.FloatField(
        verbose_name='误差范围', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品类型'


class Product(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    prodType = models.ForeignKey(ProductType, related_name='products',
                                 on_delete=models.CASCADE, verbose_name='成品名称', blank=True, null=True)
    batch = models.DateField(
        auto_now_add=True, verbose_name='成品批次', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='成品编号', blank=True, null=True)
    order = models.ForeignKey(Order, related_name='products',
                              on_delete=models.CASCADE, verbose_name='隶属订单', blank=True, null=True)
    outPos = models.ForeignKey(StorePosition, related_name='outPositions',
                                 on_delete=models.CASCADE, verbose_name='出库位', blank=True, null=True)
    inPos = models.ForeignKey(StorePosition, related_name='inPositions',
                                 on_delete=models.CASCADE, verbose_name='入库位', blank=True, null=True)
    result = models.CharField(
        max_length=20, verbose_name='质检结果', blank=True, null=True)
    reason = models.CharField(
        max_length=200, verbose_name='不合格原因', blank=True, null=True)
    status = models.ForeignKey(CommonStatus, related_name='products',
                               on_delete=models.CASCADE, verbose_name='成品状态', blank=True, null=True)

    def __str__(self):
        return self.prodType.name

    class Meta:
        verbose_name = '成品'


class ProductInfo(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    product = models.ForeignKey(Product, related_name='infos',
                                on_delete=models.CASCADE, verbose_name='隶属产品')
    name = models.CharField(max_length=200, verbose_name='信息名称')
    value = models.IntegerField(verbose_name='信息值')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品扩展'


class WorkOrder(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    status = models.ForeignKey(CommonStatus, related_name='workOrders',
                               on_delete=models.CASCADE, verbose_name='工单状态', blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='工单编号')
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    product = models.ForeignKey(Product, related_name='workOrders',
                                on_delete=models.CASCADE, verbose_name='隶属成品', blank=True, null=True)
    startTime = models.DateTimeField(
        verbose_name='开始时间', blank=True, null=True)
    endTime = models.DateTimeField(
        verbose_name='结束时间', blank=True, null=True)
    process = models.ForeignKey(Process, related_name='processes',
                                on_delete=models.CASCADE, verbose_name='目标工位', blank=True, null=True)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '工单'


class ProductStandard(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    product = models.ForeignKey(Product, related_name='standards',
                                on_delete=models.CASCADE, verbose_name='目标产品', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='标准名称', blank=True, null=True)
    expectValue = models.CharField(
        max_length=20, verbose_name='预期值', blank=True, null=True)
    realValue = models.CharField(
        max_length=20, verbose_name='实际值', blank=True, null=True)
    result = models.CharField(
        max_length=20, verbose_name='检测结果', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品标准'


class Event(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    workOrder = models.ForeignKey(WorkOrder, related_name='events',
                                  on_delete=models.CASCADE, verbose_name='隶属工单', blank=True, null=True)
    source = models.CharField(max_length=20, verbose_name='事件来源')
    title = models.CharField(max_length=20, verbose_name='事件标题')
    time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')

    def __str__(self):
        return self.title+'/'+self.time.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        verbose_name = '事件'


class Material(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='物料名称', blank=True, null=True)
    size = models.CharField(
        max_length=20, verbose_name='物料规格', blank=True, null=True)
    unit = models.CharField(
        max_length=20, verbose_name='基本单位', blank=True, null=True)
    store = models.ForeignKey(Store, related_name='materials',
                              on_delete=models.CASCADE, verbose_name='所在仓库', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '物料'


class Tool(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工具名称', blank=True, null=True)
    size = models.CharField(
        max_length=20, verbose_name='工具规格', blank=True, null=True)
    unit = models.CharField(
        max_length=20, verbose_name='基本单位', blank=True, null=True)
    store = models.ForeignKey(Store, related_name='tools',
                              on_delete=models.CASCADE, verbose_name='所在仓库', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工具'


class BOM(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    product = models.OneToOneField(ProductType, related_name='bom',
                                   on_delete=models.CASCADE, verbose_name='产品名称', blank=True, null=True)
    name = models.CharField(
        max_length=100, verbose_name='BOM名称', blank=True, null=True)
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'BOM'


class BOMContent(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    bom = models.ForeignKey(BOM, related_name='contents',
                            on_delete=models.CASCADE, verbose_name='所属BOM')
    material = models.CharField(
        max_length=100, verbose_name='物料名称')
    counts = models.IntegerField(verbose_name='物料数量', blank=True, null=True)

    def __str__(self):
        return self.material

    class Meta:
        verbose_name = 'BOM内容'


class Column(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='模型名', blank=True, null=True)
    column = models.CharField(
        max_length=4000, verbose_name='展示列', blank=True, null=True)

    def __str__(self):
        return self.column

    class Meta:
        verbose_name = '展示列'
