# import asyncio
# import logging
#
# from .client import GatewayClient
#
# logging.basicConfig(level=logging.DEBUG)
#
#
# async def handle_report(message):
#     print("Received report from server:", message)
#
#
# async def main():
#     bw_client = GatewayClient()
#
#     await bw_client.connect("304a2656b37e")
#     await bw_client.user_service.login()
#
#     await bw_client.room_service.get_rooms()
#     await bw_client.device_service.list_devices()
#     await bw_client.scene_service.get_scenes()
#     await bw_client.device_service.fetch_state("AC gateway")
#     await bw_client.device_service.set_state({
#         "device_id": 20,
#         "device_status": {
#             "state": "off"
#         }
#     })
#
#     await asyncio.Event().wait()
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
