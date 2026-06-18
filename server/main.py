import asyncio

from shared.constants import SERVER_HOST, SERVER_PORT, SNAPSHOT_INTERVAL
from server.net import GameServer
from server.game_state import GameState


async def main():
    game_state = GameState()
    server = GameServer(SERVER_HOST, SERVER_PORT, SNAPSHOT_INTERVAL, game_state)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())