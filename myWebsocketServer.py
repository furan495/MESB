import os
import json
import asyncio
import websockets

count = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


async def routeListenServer(websocket, path):
    global count
    async for message in websocket:
        while message == 'start':
            await asyncio.sleep(1)
            count += 1
            if count == 5:
                count = 0
                if os.path.exists(BASE_DIR+'/listen.txt'):
                    os.remove(BASE_DIR+'/listen.txt')
            await websocket.send(json.dumps({'res': os.path.exists(BASE_DIR+'/listen.txt')}))

start_server = websockets.serve(routeListenServer, '127.0.0.1', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
