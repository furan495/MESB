import os
import sys
import json
import django
import asyncio
import websockets
from django.db.models import Q

count = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'MESB.settings'
django.setup()


def positionSelect(obj, position):
    from app.models import Event
    try:
        return Event.objects.get(workOrder=obj, source=position).time.strftime(
            '%Y-%m-%d %H:%M:%S')
    except:
        return ''


async def routeListenServer(websocket, path):
    from app.utils import powerAna, qualAna, mateAna, storeAna
    from app.models import WorkOrder, Order, Product, OrderStatus
    global count
    async for message in websocket:
        while message == 'start':
            await asyncio.sleep(1)
            count += 1
            if count == 5:
                count = 0
                if os.path.exists(BASE_DIR+'/listen.txt'):
                    os.remove(BASE_DIR+'/listen.txt')

            workOrderList = WorkOrder.objects.filter(
                Q(status__name='等待中') | Q(status__name='加工中'))
            producing = list(
                map(lambda obj: {'key': obj.key, 'workOrder': obj.number, 'order': obj.order.number, 'LP': positionSelect(obj, '理瓶'), 'SLA': positionSelect(obj, '数粒A'), 'SLB': positionSelect(obj, '数粒B'), 'SLC': positionSelect(obj, '数粒C'), 'XG': positionSelect(obj, '旋盖'), 'CZ': positionSelect(obj, '称重'), 'TB': positionSelect(obj, '贴签'), 'HJ': positionSelect(obj, '桁架'), 'order': obj.order.number}, workOrderList))

            await websocket.send(json.dumps({'res': os.path.exists(BASE_DIR+'/listen.txt'), 'xaxis': list(map(lambda obj: obj.number, Order.objects.all())), 'powerana': powerAna(), 'qualana': qualAna(), 'mateana': mateAna(), 'storeana': storeAna(), 'producing': producing}))

start_server = websockets.serve(routeListenServer, '192.168.2.3', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
