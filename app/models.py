import time
from django.db import models

# Create your models here.

# 暂无工具,bom,物料相关表


class Document(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=30, verbose_name='文档名称', blank=True, null=True)
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
        max_length=20, verbose_name='车间名称', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='车间编号', blank=True, null=True)
    descriptions = models.CharField(
        max_length=200, verbose_name='车间描述', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '车间'


class ProcessRoute(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工艺名称', blank=True, null=True)
    data = models.CharField(
        max_length=4000, verbose_name='工艺内容', blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='工艺描述', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工艺路线'


class Department(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=10, verbose_name='部门', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '部门'


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

    USER_GENDER = (
        ('1', '男'),
        ('2', '女'),
    )

    key = models.AutoField(primary_key=True, verbose_name='主键')
    department = models.ForeignKey(
        Department, related_name='members', on_delete=models.CASCADE, verbose_name='部门', blank=True, null=True)
    role = models.ForeignKey(Role, related_name='users',
                             on_delete=models.CASCADE, verbose_name='角色', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='姓名', blank=True, null=True)
    password = models.CharField(
        max_length=20, verbose_name='密码', blank=True, null=True)
    gender = models.CharField(
        max_length=2, verbose_name='性别', choices=USER_GENDER, blank=True, null=True)
    phone = models.CharField(
        max_length=20, verbose_name='电话', blank=True, null=True)
    company = models.CharField(
        max_length=20, verbose_name='公司', blank=True, null=True)

    def __str__(self):
        return '%s/%s/%s/%s/%s' % (str(self.key), self.name, self.gender, self.role, self.phone)

    class Meta:
        verbose_name = '用户'


class OrderStatus(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='订单状态', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '订单状态'


class OrderType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='订单类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '订单类型'


class Order(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    status = models.ForeignKey(OrderStatus, related_name='status',
                               on_delete=models.CASCADE, verbose_name='订单状态', default='1', blank=True, null=True)
    orderType = models.ForeignKey(OrderType, related_name='types',
                                  on_delete=models.CASCADE, verbose_name='订单类型', blank=True, null=True)
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)
    batch = models.CharField(
        max_length=20, verbose_name='订单批次', blank=True, null=True)
    scheduling = models.CharField(max_length=50,
                                  verbose_name='订单排产', blank=True, null=True)
    number = models.CharField(max_length=20,
                              verbose_name='订单编号', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True,
                                      verbose_name='创建时间')
    description = models.CharField(
        max_length=200, verbose_name='订单描述', blank=True, null=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = '订单'


class BottleState(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='瓶子状态', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '瓶子状态'


class Bottle(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    order = models.ForeignKey(Order, related_name='bottles',
                              on_delete=models.CASCADE, verbose_name='隶属订单', blank=True, null=True)
    status = models.ForeignKey(BottleState, related_name='bottles',
                               on_delete=models.CASCADE, verbose_name='瓶子状态', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='瓶号', blank=True, null=True)
    color = models.CharField(
        max_length=20, verbose_name='颜色', blank=True, null=True)
    red = models.IntegerField(verbose_name='红粒个数', blank=True, null=True)
    green = models.IntegerField(verbose_name='绿粒个数', blank=True, null=True)
    blue = models.IntegerField(verbose_name='蓝粒个数', blank=True, null=True)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '瓶子'


class ProductLine(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    workShop = models.ForeignKey(WorkShop, related_name='productLines',
                                 on_delete=models.CASCADE, verbose_name='隶属车间')
    name = models.CharField(max_length=20, verbose_name='产线名称')
    number = models.CharField(max_length=20, verbose_name='产线编号')
    description = models.CharField(max_length=200, verbose_name='产线描述')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产线'


class Process(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    skip = models.BooleanField(verbose_name='可否跳过', default=False)
    route = models.ForeignKey(ProcessRoute, related_name='processes',
                              on_delete=models.CASCADE, verbose_name='隶属工艺')
    name = models.CharField(max_length=20, verbose_name='工序名称')
    path = models.CharField(
        max_length=200, verbose_name='工序图片', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工序'


class WorkPosition(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    """ productLine = models.ForeignKey(ProductLine, related_name='workPositions',
                                    on_delete=models.CASCADE, verbose_name='隶属产线') """
    process = models.OneToOneField(Process, related_name='process',
                                   on_delete=models.CASCADE, verbose_name='对应工序')
    name = models.CharField(max_length=20, verbose_name='工位名')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工位'


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
    deviceType = models.ForeignKey(DeviceType, related_name='devices',
                                   on_delete=models.CASCADE, verbose_name='设备类型', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='设备名称', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='设备编号', blank=True, null=True, default=str(time.time()*1000))
    joinTime = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')
    exitTime = models.DateTimeField(auto_now=True, verbose_name='报废时间')
    factory = models.CharField(
        max_length=20, verbose_name='设备厂家', blank=True, null=True, default='XXX工厂')
    facTime = models.CharField(
        max_length=20, verbose_name='出厂日期', blank=True, null=True, default='2020-02-13')
    facPeo = models.CharField(
        max_length=20, verbose_name='厂家联系人', blank=True, null=True, default='XXX先生')
    facPho = models.CharField(
        max_length=20, verbose_name='厂家电话', blank=True, null=True, default='13312345678')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '设备'


class DeviceState(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    device = models.ForeignKey(Device, related_name='states',
                               on_delete=models.CASCADE, verbose_name='目标设备')
    isOpen = models.BooleanField(verbose_name='是否开机', default=False)
    openTime = models.CharField(
        max_length=30, verbose_name='开机时间', blank=True, null=True)
    closeTime = models.CharField(
        max_length=30, verbose_name='关机时间', blank=True, null=True)
    isWork = models.BooleanField(verbose_name='是否工作', default=False)
    workStart = models.CharField(
        max_length=30, verbose_name='开始工作时间', blank=True, null=True)
    workEnd = models.CharField(
        max_length=30, verbose_name='结束工作时间', blank=True, null=True)
    isFault = models.BooleanField(verbose_name='是否故障', default=False)
    faultTime = models.CharField(
        max_length=30, verbose_name='故障时间', blank=True, null=True)
    faultLevel = models.CharField(
        max_length=20, verbose_name='故障等级', blank=True, null=True)
    faultReason = models.CharField(
        max_length=200, verbose_name='故障原因', blank=True, null=True)
    isRepair = models.BooleanField(verbose_name='是否返修', default=False)
    repairStart = models.CharField(
        max_length=30, verbose_name='返修开始时间', blank=True, null=True)
    repairEnd = models.CharField(
        max_length=30, verbose_name='返修结束时间', blank=True, null=True)
    repairResult = models.BooleanField(verbose_name='返修结果', default=False)

    def __str__(self):
        return self.device.name

    class Meta:
        verbose_name = '设备状态'


class WorkOrderStatus(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工单状态', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工单状态'


class WorkOrder(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    order = models.ForeignKey(Order, related_name='workOrders',
                              on_delete=models.CASCADE, verbose_name='隶属订单')
    status = models.ForeignKey(WorkOrderStatus, related_name='status',
                               on_delete=models.CASCADE, verbose_name='工单状态', blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='工单编号')
    bottle = models.CharField(
        max_length=20, verbose_name='工单瓶号', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    startTime = models.CharField(
        max_length=20, verbose_name='开始时间', blank=True, null=True)
    endTime = models.CharField(
        max_length=20, verbose_name='结束时间', blank=True, null=True)
    description = models.CharField(max_length=200, verbose_name='工单描述')

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '工单'


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
    workShop = models.ForeignKey(WorkShop, related_name='stores',
                                 on_delete=models.CASCADE, verbose_name='隶属车间', blank=True, null=True)
    storeType = models.ForeignKey(StoreType, related_name='stores',
                                  on_delete=models.CASCADE, verbose_name='仓库类型', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='仓库名称', blank=True, null=True)
    number = models.CharField(
        max_length=20, verbose_name='仓库编号', blank=True, null=True)
    dimensions = models.CharField(
        max_length=20, verbose_name='仓库规模',  blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '仓库'


class StroePosition(models.Model):
    POSITION_STATUS = (
        ('1', '有盘'),
        ('2', '无盘'),
        ('3', '有料'),
        ('4', '无料'),
    )
    key = models.AutoField(primary_key=True, verbose_name='主键')
    store = models.ForeignKey(Store, related_name='positions',
                              on_delete=models.CASCADE, verbose_name='隶属仓库')
    status = models.CharField(
        max_length=2, verbose_name='仓位状态', choices=POSITION_STATUS, blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='仓位编号')

    def __str__(self):
        return self.number+'/'+self.status+'/'+str(self.key)

    class Meta:
        verbose_name = '仓位'


class Pallet(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    position = models.OneToOneField(StroePosition, related_name='positions',
                                    on_delete=models.CASCADE, verbose_name='隶属仓位')
    number = models.CharField(max_length=20, verbose_name='托盘编号')
    rate = models.FloatField(verbose_name='利用率', default=0.0)
    hole1 = models.BooleanField(verbose_name='孔位1状态', default=False)
    hole2 = models.BooleanField(verbose_name='孔位2状态', default=False)
    hole3 = models.BooleanField(verbose_name='孔位3状态', default=False)
    hole4 = models.BooleanField(verbose_name='孔位4状态', default=False)
    hole5 = models.BooleanField(verbose_name='孔位5状态', default=False)
    hole6 = models.BooleanField(verbose_name='孔位6状态', default=False)
    hole7 = models.BooleanField(verbose_name='孔位7状态', default=False)
    hole8 = models.BooleanField(verbose_name='孔位8状态', default=False)
    hole9 = models.BooleanField(verbose_name='孔位9状态', default=False)
    hole1Content = models.CharField(
        max_length=20, verbose_name='孔位1内容', blank=True, null=True)
    hole2Content = models.CharField(
        max_length=20, verbose_name='孔位2内容', blank=True, null=True)
    hole3Content = models.CharField(
        max_length=20, verbose_name='孔位3内容', blank=True, null=True)
    hole4Content = models.CharField(
        max_length=20, verbose_name='孔位4内容', blank=True, null=True)
    hole5Content = models.CharField(
        max_length=20, verbose_name='孔位5内容', blank=True, null=True)
    hole6Content = models.CharField(
        max_length=20, verbose_name='孔位6内容', blank=True, null=True)
    hole7Content = models.CharField(
        max_length=20, verbose_name='孔位7内容', blank=True, null=True)
    hole8Content = models.CharField(
        max_length=20, verbose_name='孔位8内容', blank=True, null=True)
    hole9Content = models.CharField(
        max_length=20, verbose_name='孔位9内容', blank=True, null=True)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '托盘'


class Operate(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    pallet = models.ForeignKey(Pallet, related_name='operations',
                               on_delete=models.CASCADE, verbose_name='目标托盘', blank=True, null=True)
    device = models.ForeignKey(Device, related_name='operations',
                               on_delete=models.CASCADE, verbose_name='目标设备', blank=True, null=True)
    order = models.ForeignKey(Order, related_name='operations',
                              on_delete=models.CASCADE, verbose_name='目标订单', blank=True, null=True)
    processRuote = models.ForeignKey(ProcessRoute, related_name='operations',
                                     on_delete=models.CASCADE, verbose_name='目标工艺', blank=True, null=True)
    store = models.ForeignKey(Store, related_name='operations',
                              on_delete=models.CASCADE, verbose_name='目标仓库', blank=True, null=True)
    document = models.ForeignKey(Document, related_name='operations',
                                 on_delete=models.CASCADE, verbose_name='目标文档', blank=True, null=True)
    role = models.ForeignKey(Role, related_name='operations',
                             on_delete=models.CASCADE, verbose_name='目标角色', blank=True, null=True)
    name = models.CharField(
        max_length=20, verbose_name='操作名称', blank=True, null=True)
    operator = models.CharField(
        max_length=20, verbose_name='操作人', blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '操作'


class ProductType(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='产品类型', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品类型'


class Product(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    workOrder = models.OneToOneField(WorkOrder, related_name='workOrder',
                                     on_delete=models.CASCADE, verbose_name='对应工单')
    pallet = models.ForeignKey(Pallet, related_name='products',
                               on_delete=models.CASCADE, verbose_name='存放托盘')
    prodType = models.ForeignKey(ProductType, related_name='products',
                                 on_delete=models.CASCADE, verbose_name='产品类型')
    name = models.CharField(max_length=20, verbose_name='产品名称')
    number = models.CharField(max_length=20, verbose_name='产品编号')
    description = models.CharField(max_length=200, verbose_name='产品描述')
    batch = models.DateTimeField(auto_now_add=True, verbose_name='产品批次')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品'


class ProductStandard(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    product = models.ForeignKey(Product, related_name='standards',
                                on_delete=models.CASCADE, verbose_name='操作人')
    name = models.CharField(max_length=20, verbose_name='标准名称')
    expectValue = models.FloatField(verbose_name='预期值')
    realValue = models.FloatField(verbose_name='实际值')
    result = models.CharField(max_length=20, verbose_name='检测结果')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '产品标准'


class Event(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    workOrder = models.ForeignKey(WorkOrder, related_name='events',
                                  on_delete=models.CASCADE, verbose_name='隶属工单', blank=True, null=True)
    bottle = models.CharField(
        max_length=20, verbose_name='事件瓶号', blank=True, null=True)
    source = models.CharField(max_length=20, verbose_name='事件来源')
    title = models.CharField(max_length=20, verbose_name='事件标题')
    time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')

    def __str__(self):
        return self.title+'/'+self.time.strftime('%Y-%m-%d %H:%M:%S')

    class Meta:
        verbose_name = '事件'
