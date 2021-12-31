import os

import aiosqlite as aiosqlite
import httpx
from sanic import Sanic, json
from sanic.log import logger

from bot.caching import CACHE
from bot.configs import bot_url, webhook, api_key
from bot.controllers import health, updates


app = Sanic('TGProxyBot')


async def register_webhook():
    app.router.reset()
    app.add_route(updates, app.ctx.tg_webhook, methods=['POST'])
    app.router.finalize()
    return


@app.before_server_start
async def sanity_check(*args):  # noqa
    required_vars = ('TG_BASE_URL', 'CALLBACK_URL_BASE', 'PROXY_TO')
    bot_key = os.path.exists('/run/secrets/BOT_API_KEY')
    if not all([os.environ.get(var) for var in required_vars]) or not bot_key:
        logger.error('Configuration incomplete. Make sure all .env.template vars are in your environment. '
                     'Make sure you have a bot key saved under a `BOT_API_KEY` Docker secret.')
        exit('Invalid configs.')


@app.before_server_start
async def set_webhook(*args):  # noqa
    url = await bot_url() + 'setWebhook'
    wh = await webhook()
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data={'url': wh})
        if response.json()['ok']:
            app.ctx.tg_webhook = await api_key()
            await register_webhook()
        else:
            logger.error(f'Bad response from Telegram: {response.content}')


@app.before_server_start
async def storage_setup(*args):  # noqa
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bans 
            (
                tg_id INTEGER PRIMARY KEY,
                ban_timestamp INTEGER NOT NULL
            );
            """
        )
        await db.commit()

        # also sync cache to DB
        ban_list = []
        async with db.execute("SELECT tg_id FROM bans") as cursor:
            async for row in cursor:
                ban_list.append(row[0])
        CACHE['ban_list'] = ban_list
        CACHE['synced'] = True


app.add_route(lambda _: json({}), '/')
app.add_route(health, '/health', methods=['GET'])


app.run(
    host=os.environ.get('HOST'),
    port=os.environ.get('PORT'),
    debug=bool(int(os.environ.get('DEBUG'))),
    auto_reload=bool(int(os.environ.get('AUTO_RELOAD'))),
    workers=int(os.environ.get('WORKERS')),
    access_log=bool(int(os.environ.get('ACCESS_LOG')))
)
