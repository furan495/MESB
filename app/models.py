from django.db import models

# Create your models here.

# 暂无工具、设备,bom,物料相关表


class WorkShop(models.Model):

    WORKSHOP_STATUS = (
        ('1', '使用中'),
        ('2', '已弃用'),
    )
    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(max_length=20, verbose_name='车间名称')
    number = models.CharField(max_length=20, verbose_name='车间编号')
    descriptions = models.CharField(max_length=200, verbose_name='车间描述')
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    status = models.CharField(
        max_length=2, verbose_name='车间状态', choices=WORKSHOP_STATUS)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '车间'


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
        return '%s/%s/%s/%s/%s'%(str(self.key),self.name,self.gender,self.role,self.phone)

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
    number = models.DateTimeField(
        auto_now_add=True, verbose_name='订单编号', blank=True, null=True)
    createTime = models.DateTimeField(
        auto_now_add=True, verbose_name='创建时间', blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='订单描述', blank=True, null=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = '订单'


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


class WorkPosition(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    productLine = models.ForeignKey(ProductLine, related_name='workPositions',
                                    on_delete=models.CASCADE, verbose_name='隶属产线')
    name = models.CharField(max_length=20, verbose_name='工位名')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工位'


class ProcessRoute(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    name = models.CharField(
        max_length=20, verbose_name='工艺名称', blank=True, null=True)
    data = models.CharField(
        max_length=5000, verbose_name='工艺内容', blank=True, null=True)
    description = models.CharField(
        max_length=200, verbose_name='工艺描述', blank=True, null=True)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    creator = models.CharField(
        max_length=20, verbose_name='创建人', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工艺路线'


class Process(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    route = models.ForeignKey(ProcessRoute, related_name='processes',
                              on_delete=models.CASCADE, verbose_name='隶属工艺')
    name = models.CharField(max_length=20, verbose_name='工序名称')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '工序'


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
    route = models.ForeignKey(ProcessRoute, related_name='workOrders',
                              on_delete=models.CASCADE, verbose_name='选用工艺')
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
                                 on_delete=models.CASCADE, verbose_name='隶属车间')
    storeType = models.ForeignKey(StoreType, related_name='stores',
                                  on_delete=models.CASCADE, verbose_name='仓库类型')
    name = models.CharField(max_length=20, verbose_name='仓库名称')
    number = models.CharField(max_length=20, verbose_name='仓库编号')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '仓库'


class StroePosition(models.Model):
    key = models.AutoField(primary_key=True, verbose_name='主键')
    store = models.ForeignKey(Store, related_name='positions',
                              on_delete=models.CASCADE, verbose_name='隶属仓库')
    number = models.CharField(max_length=20, verbose_name='仓位编号')

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '仓位'


class Pallet(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    position = models.OneToOneField(StroePosition, related_name='positions',
                                    on_delete=models.CASCADE, verbose_name='隶属仓位')
    number = models.CharField(max_length=20, verbose_name='托盘编号')
    hole1 = models.BooleanField(verbose_name='孔位1状态')
    hole2 = models.BooleanField(verbose_name='孔位2状态')
    hole3 = models.BooleanField(verbose_name='孔位3状态')
    hole4 = models.BooleanField(verbose_name='孔位4状态')
    hole5 = models.BooleanField(verbose_name='孔位5状态')
    hole6 = models.BooleanField(verbose_name='孔位6状态')
    hole7 = models.BooleanField(verbose_name='孔位7状态')
    hole8 = models.BooleanField(verbose_name='孔位8状态')
    hole9 = models.BooleanField(verbose_name='孔位9状态')
    hole1Content = models.CharField(max_length=20, verbose_name='孔位1内容')
    hole2Content = models.CharField(max_length=20, verbose_name='孔位2内容')
    hole3Content = models.CharField(max_length=20, verbose_name='孔位3内容')
    hole4Content = models.CharField(max_length=20, verbose_name='孔位4内容')
    hole5Content = models.CharField(max_length=20, verbose_name='孔位5内容')
    hole6Content = models.CharField(max_length=20, verbose_name='孔位6内容')
    hole7Content = models.CharField(max_length=20, verbose_name='孔位7内容')
    hole8Content = models.CharField(max_length=20, verbose_name='孔位8内容')
    hole9Content = models.CharField(max_length=20, verbose_name='孔位9内容')

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = '托盘'


class Product(models.Model):

    key = models.AutoField(primary_key=True, verbose_name='主键')
    pallet = models.ForeignKey(Pallet, related_name='products',
                               on_delete=models.CASCADE, verbose_name='存放托盘')
    name = models.CharField(max_length=20, verbose_name='产品名称')
    user = models.CharField(
        max_length=20, verbose_name='操作人', blank=True, null=True)
    number = models.CharField(max_length=20, verbose_name='产品编号')
    description = models.CharField(max_length=200, verbose_name='产品描述')
    prodType = models.CharField(
        max_length=20, verbose_name='产品类型', blank=True, null=True)
    batch = models.CharField(max_length=20, verbose_name='产品批次')
    pic = models.FileField(upload_to='static/product', verbose_name='产品图片')
    operateTime = models.DateTimeField(auto_now=True, verbose_name='操作时间')

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
    source = models.CharField(max_length=20, verbose_name='事件来源')
    bottle = models.CharField(max_length=20, verbose_name='瓶号')
    title = models.CharField(max_length=20, verbose_name='事件标题')
    time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')

    def __str__(self):
        return self.title+'/'+str(self.time)

    class Meta:
        verbose_name = '事件'
