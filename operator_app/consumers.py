from channels.consumer import AsyncConsumer


class YourConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        await self.send({"type": "websocket.accept"})

    async def websocket_receive(self, text_data):
        # with open('call_client.txt') as f:
        #     numb_phone = f.read()
        # if numb_phone:
        #     await self.send({
        #         "type": "websocket.send",
        #         "text": numb_phone
        #     })
        await self.send({
                    "type": "websocket.send",
                    "text": 'numb_phone'
                })

    async def websocket_disconnect(self, event):
        pass
