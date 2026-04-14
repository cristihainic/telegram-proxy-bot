![build](https://github.com/cristihainic/telegram-proxy-bot/actions/workflows/tests.yml/badge.svg)

# Telegram Proxy Bot

A self-hosted Telegram bot that turns any chat — your DMs or a shared group — into a **shared inbox**. Incoming messages from users land in your chat; your replies go out under the bot's identity. Nobody on the outside ever sees who's actually behind it.

### Who's it for?

- **Channel / Group / Forum admins** — collect message proposals, submissions, or reports from your audience. Admins discuss privately in the bot's group, then reply back to the submitter through the bot.
- **Customer support desks** — a team of operators in a shared group handles customer DMs together. Tap **[Reply]** to route your response back to the sender; your teammates see the context and stay in sync.
- **Community & channel admins** — field questions from your followers from one place, without exposing personal accounts or passing a phone around.
- **Sales & leads inbox** — every prospect DM lands in your sales team's group. Any rep can pick it up; no leads fall through the cracks.
- **Tip lines & anonymous feedback** — student-to-teacher, employee-to-HR, reader-to-editor. Senders stay anonymous if they want; operators always stay anonymous to senders.
- **Solo privacy** — communicate with strangers (marketplace buyers, forum contacts, one-off acquaintances) without handing over your real Telegram account.

### What it does

- **Forwards** every incoming DM to your chosen chat — text, photos, documents, voice notes, video, stickers, anything.
- **Single-tap Reply / Ban** — inline buttons under every incoming message. Reply once, any message type, and the user gets it from the bot. No ID copying, no command syntax.
- **Multi-operator aware** — per-operator reply state, so teammates in a support group don't step on each other.
- **Ban management** — `/ban <id>`, `/unban <id>`, `/bans` for a formatted list with names and dates. Slash commands appear in Telegram's built-in `/` menu.
- **Self-hosted** — your server, your data. No per-seat pricing, no third-party vendor, no message logs in someone else's cloud.
- **No message persistence** — the bot doesn't store message content. GDPR-friendly by design.

### Server requirements

This is a _very_ lightweight bot. The cheapest VPS or Raspberry Pi will do.

- **1 CPU core, 1 GB RAM** — comfortable headroom; 512 MB also works for low-volume installs
- **~300 MB disk** (Docker image + tiny SQLite DB for bans)
- **Linux host with Docker + Docker Compose** (any modern distro)
- **Public HTTPS endpoint** — Telegram requires HTTPS for webhooks. Use a domain with a TLS certificate (Caddy or nginx + Let's Encrypt is the easy route) or [ngrok](https://ngrok.com) for testing.

### Get your bot running
1. Clone this repo on the server which you want to run the bot from and `cd` into the root directory;
2. Create a `secrets` directory with a `bot_api_key` file containing your Telegram bot key:
    ```
    mkdir secrets
    printf "123asd-mybotkey-blabla" > secrets/bot_api_key
    ```
3. `cp .env.template .env` and modify the latter to your liking;
4. **Disable your bot's Group Privacy mode** so it can see all messages in the PROXY_TO group (needed for the Reply button flow):
   - DM [@BotFather](https://t.me/BotFather) → `/mybots` → select your bot → **Bot Settings** → **Group Privacy** → **Turn off**
   - If your bot is already in the group, remove it and re-add it for the privacy change to take effect
   - Without this, Telegram only delivers slash commands and @mentions to your bot — regular operator replies will never reach it
5. `docker compose up` and profit.

### Experience the proxy bot awesomeness
#### Receiving messages 
The bot forwards each user message into the PROXY_TO chat, then follows it with a compact action bar containing the user's ID and two inline buttons:

```
[Forwarded from John Smith: "Hi there"]
ID: 19612312371
  [Reply]  [Ban]
```

For users with strict forward privacy settings (where the forward header just says "Forwarded from a user"), the action bar's ID gives you a handle to identify them — and when you tap **Reply**, the confirmation toast shows their full name since the bot caches it server-side.

#### Replying to messages
Tap **Reply** on any action bar. The bot posts a persistent reminder in the chat:
```
📝 Replying to John Smith (@JS666). Send any message — auto-cancels in 10 min.
```
Your next message in the PROXY_TO chat — **any type**: text, photo, document, audio, voice, video, sticker — gets delivered to the user as if sent by the bot. The reminder is removed and a confirmation `✓ Sent to John Smith (@JS666)` is posted in its place.

If you don't send anything within 10 minutes, the pending reply state auto-expires (the reminder stays as a record of the abandoned reply).

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

### Need help setting it up?
If you'd rather not deal with Docker, domains, TLS certificates or BotFather configuration, I can install and configure the bot on your server (or provision a new one) and hand you a working setup. Customization, integrations, and maintenance contracts are also on the table. Drop me a line at **hey@cristi.rocks**.

### Development
Contributions are welcome! 

When developing, build the project with the `INSTALL_DEV` build argument set to `true` e.g, 

```docker compose build --build-arg INSTALL_DEV=true```

Feel free to work on any of the known issues / change requests or open a new one [here](https://github.com/cristihainic/telegram-proxy-bot/issues).
