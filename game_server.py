import asyncio
import json
import websockets

players = {}
enemies = {}
game_started = False

async def broadcast_message(message):
    """Отправка сообщения всем клиентам."""
    await asyncio.gather(
        *[ws.send(json.dumps(message)) for ws in players.keys()],
        return_exceptions=True
    )

async def broadcast_game_state():
    """Рассылка состояния игры."""
    while game_started:
        game_state = {
            "type": "game_update",
            "players": [
                {"player_id": p["player_id"], "x": p["x"], "y": p["y"], "color": p["color"]}
                for p in players.values()
            ],
            "enemies": [
                {"enemy_id": e["enemy_id"], "x": e["x"], "y": e["y"]}
                for e in enemies.values()
            ]
        }
        print(f"Broadcasting game state: {json.dumps(game_state)}")  # Log the state being broadcasted
        await broadcast_message(game_state)
        await asyncio.sleep(0.05)


async def handle_client(websocket):
    global players, game_started

    client_id = str(id(websocket))

    if websocket not in players:
        players[websocket] = {
            "player_id": client_id,
            "x": 0,
            "y": 0,
            "ready": False,
            "color": assign_player_color(len(players))
        }
        print(f"Player {client_id} connected.")

    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received message from {client_id}: {data}")  # Log incoming data

            if data['type'] == 'player_move':
                # Обновление позиции игрока
                player_id = data['player_id']
                players[player_id]['x'] = data['x']
                players[player_id]['y'] = data['y']
                print(f"Updated position for player {player_id}: ({data['x']}, {data['y']})")

                # Отправка обновлений всем клиентам
                await broadcast_game_state()

            elif data['type'] == 'enemy_move':
                # Обновление позиции врага
                enemy_id = data['enemy_id']
                if enemy_id in enemies:
                    enemies[enemy_id]['x'] = data['x']
                    enemies[enemy_id]['y'] = data['y']
                    print(f"Updated position for enemy {enemy_id}: ({data['x']}, {data['y']})")

                # Отправка обновлений всем клиентам
                await broadcast_game_state()

            elif data['type'] == 'button_press' and data['button'] == 'play':
                if not game_started:
                    # Старт игры по запросу
                    await start_game()

    except websockets.exceptions.ConnectionClosed:
        del players[websocket]
        print(f"Player {client_id} disconnected.")


async def start_game():
    global game_started
    game_started = True
    print("Game starting!")

    create_enemies()  # Создание врагов

    # Отправка обновленного состояния игры (включая позиции врагов) всем клиентам
    game_state = {
        "type": "game_update",
        "players": [
            {"player_id": p["player_id"], "x": p["x"], "y": p["y"], "color": p["color"]}
            for p in players.values()
        ],
        "enemies": [
            {"enemy_id": e["enemy_id"], "x": e["x"], "y": e["y"]}
            for e in enemies.values()
        ]
    }
    await broadcast_message(game_state)

    # Рассылка отсчета времени
    for count in range(3, 0, -1):
        await broadcast_message({"type": "countdown", "value": str(count)})
        await asyncio.sleep(1)
    await broadcast_message({"type": "countdown", "value": "GO!"})
    await broadcast_game_state()

def create_enemies():
    global enemies
    for i, (x, y) in enumerate([(10, 10), (20, 20), (30, 30)]):
        enemy_id = f"enemy_{i + 1}"
        enemies[enemy_id] = {"enemy_id": enemy_id, "x": x, "y": y}

def assign_player_color(index):
    colors = ["red", "blue", "green", "yellow"]
    return colors[index % len(colors)]

async def main():
    async with websockets.serve(handle_client, "localhost", 12345):
        print("Server running on ws://localhost:12345")
        await asyncio.Future()  # Ожидаем пока сервер не будет остановлен

asyncio.run(main())















