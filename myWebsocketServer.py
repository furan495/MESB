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


async def routeListenServer(websocket, path):
    from app.models import WorkOrder, Order, Product
    global count
    async for message in websocket:
        while message == 'start':
            await asyncio.sleep(1)
            count += 1
            if count == 5:
                count = 0
                if os.path.exists(BASE_DIR+'/listen.txt'):
                    os.remove(BASE_DIR+'/listen.txt')

            boards = list(map(lambda obj: {'key': obj.key, 'line': obj.line.name, 'number': obj.number,
                                           'expectYields': len(WorkOrder.objects.filter(Q(order=obj))), 'realYields': len(WorkOrder.objects.filter(Q(status__name='已完成', order=obj))), 'state': obj.line.state.name, 'rate': round(len(Product.objects.filter(Q(prodType__name='合格', workOrder__order=obj))) / len(WorkOrder.objects.filter(Q(order=obj))), 2)}, Order.objects.all()))

            await websocket.send(json.dumps({'res': os.path.exists(BASE_DIR+'/listen.txt'), 'boards': boards}))

start_server = websockets.serve(routeListenServer, '192.168.1.103', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
