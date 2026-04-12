![build](https://github.com/cristihainic/telegram-proxy-bot/actions/workflows/tests.yml/badge.svg)

# Telegram Proxy Bot

A bot to receive and send messages on Telegram without revealing your identity to other users. 

### Features
This bot:
- forwards all messages it receives to a chat (DM or group chat) of your liking;
- proxies messages back to users without revealing your identity;
- supports **any message type** for replies — text, photos, documents, audio, voice, video, stickers;
- provides **inline buttons** (Reply, Ban) on each incoming message for single-tap handling;
- exposes operator commands via Telegram's native `/` menu;
- does **not** store the content of messages it proxies - no GDPR hassle.

### Get your bot running
1. Clone this repo on the server which you want to run the bot from and `cd` into the root directory;
2. Create a `secrets` directory with a `bot_api_key` file containing your Telegram bot key:
    ```
    mkdir secrets
    printf "123asd-mybotkey-blabla" > secrets/bot_api_key
    ```
3. `cp .env.template .env` and modify the latter to your liking;
4. `docker compose up` and profit.

### Experience the proxy bot awesomeness
#### Receiving messages 
To allow you to reply to users and to bypass some annoying Telegram behavior (e.g., no "Forwarded from..." header is included if a user sends you an audio file), the bot sends a "pre-flight" message before every proxied message. The pre-flight shows the sender's name and ID, with two inline buttons:

```
From: John Smith (@JS666)
ID: 19612312371
[Reply]  [Ban]
```

Then the actual forwarded message follows.

You can disable pre-flight messages entirely by setting `PREFLIGHT=0` in your `.env` (note: this also hides the Reply/Ban buttons).

#### Replying to messages
Tap **Reply** on any pre-flight message. Telegram shows a toast:
```
Replying to John Smith (@JS666). Send your next message.
```
Your next message in the PROXY_TO chat — **any type**: text, photo, document, audio, voice, video, sticker — will be delivered to the user as if sent by the bot. A confirmation `✓ Sent to John` is posted in the group.

If you don't send anything within 10 minutes, the pending reply state auto-expires.

#### Banning, unbanning, listing bans
Operator commands appear in Telegram's `/` menu inside the PROXY_TO chat:

- **`/ban <user_id>`** — ban a user by ID. (You can also tap the **Ban** button on a pre-flight message.)
- **`/unban <user_id>`** — unban a user.
- **`/bans`** — list all banned users with names and ban dates:

```
Banned users:
• John Smith (@JS666) — ID 19612312371 — 2026-04-12
• Jane Doe — ID 98765 — 2026-04-10
```

### Development
Contributions are welcome! 

When developing, build the project with the `INSTALL_DEV` build argument set to `true` e.g, 

```docker compose build --build-arg INSTALL_DEV=true```

Feel free to work on any of the known issues / change requests or open a new one [here](https://github.com/cristihainic/telegram-proxy-bot/issues).
