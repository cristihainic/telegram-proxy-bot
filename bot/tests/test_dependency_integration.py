"""Integration tests verifying upgraded dependencies work correctly."""
import json
import os
import tempfile

import aiofiles
import aiosqlite
import httpx
from sanic import Sanic, json as sanic_json, Request


async def test_aiosqlite_crud():
    """Verify aiosqlite async context manager, execute, fetchone, fetchall."""
    async with aiosqlite.connect(':memory:') as db:
        await db.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
        await db.execute('INSERT INTO test (value) VALUES (?)', ('hello',))
        await db.execute('INSERT INTO test (value) VALUES (?)', ('world',))
        await db.commit()

        async with db.execute('SELECT value FROM test WHERE id = 1') as cursor:
            row = await cursor.fetchone()
            assert row[0] == 'hello'

        async with db.execute('SELECT value FROM test ORDER BY id') as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 2
            assert rows[1][0] == 'world'

        await db.execute('DELETE FROM test WHERE id = 1')
        await db.commit()
        async with db.execute('SELECT COUNT(*) FROM test') as cursor:
            count = (await cursor.fetchone())[0]
            assert count == 1


async def test_aiofiles_read_write():
    """Verify aiofiles can async read and write."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        path = f.name

    try:
        async with aiofiles.open(path, mode='w') as f:
            await f.write('async-content')

        async with aiofiles.open(path, mode='r') as f:
            content = await f.read()
        assert content == 'async-content'
    finally:
        os.unlink(path)


async def test_httpx_async_client():
    """Verify httpx.AsyncClient can be instantiated and used."""
    async with httpx.AsyncClient() as client:
        assert client is not None
        assert not client.is_closed
    assert client.is_closed


async def test_sanic_app_creation_and_routing():
    """Verify Sanic app, route registration, and ctx work."""
    test_app = Sanic('TestDepApp')

    @test_app.get('/test')
    async def handler(request: Request):
        return sanic_json({'status': 'ok'})

    test_app.ctx.custom_value = 42

    assert test_app.name == 'TestDepApp'
    assert test_app.ctx.custom_value == 42


async def test_stdlib_json_compact_matches_ujson_format():
    """Verify stdlib json with compact separators produces the same
    output as ujson.dumps (no spaces, lowercase booleans)."""
    data = {
        "id": 90422868,
        "is_bot": False,
        "first_name": "John",
        "last_name": "Smith",
        "username": "Js66"
    }
    result = json.dumps(data, separators=(',', ':'))
    expected = '{"id":90422868,"is_bot":false,"first_name":"John","last_name":"Smith","username":"Js66"}'
    assert result == expected
