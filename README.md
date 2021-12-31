![build](https://github.com/cristihainic/telegram-proxy-bot/actions/workflows/tests.yml/badge.svg)

# Telegram Proxy Bot

A bot to receive and send messages on Telegram without revealing your identity to other users. 

### Features
This bot:
- forwards all messages it receives to a chat (DM or group chat) of your liking;
- proxies messages back to users without revealing your identity.
- does **not** store messages.

### Get your bot running
1. Clone this repo on the server which you want to run the bot from and `cd` into the root directory;
2. Create a `secrets` directory with a `bot_api_key` file containing your Telegram bot key:
    ```
    mkdir secrets
    printf "123asd-mybotkey-blabla" > secrets/bot_api_key
    ```
3. `cp .env.template .env` and modify the latter to your liking;
4. `docker-compose up` and profit.

### Experience the proxy bot awesomeness
#### Receiving messages 
To allow you to reply to users and to bypass some annoying Telegram behavior (e.g., no "Forwarded from..." message is included if a user sends you an audio files, leaving you clueless as to _who_ sent the message), the bot will send "pre-flight" messages for all messages it proxies to you. These pre-flight messages include the details of the sender, in the form of:
```
Incoming message from: 
{
    "id": 19612312371,
    "is_bot":false,
    "first_name":"John",
    "last_name":"Smith",
    "username":"JS666",
    "language_code":"en"
}
```
Then, the actual forwarded message ensues.

#### Sending messages
The Telegram ID above is the unique identifier of a user throughout the app. To have the bot send a reply to a user, **reply** to any of the bot's messages or forwards with this:

```
send || <user id> || your message here
```

So, if we wanted to send a message back to John Smith, we'd **reply to any** of the bot's messages with:
```
send || 19612312371 || Hi John, nice to meet you. You have no idea who's behind this bot.
```

John will then receive the message from the bot.


### Development
Contributions are welcome! 

When developing, build the project with the `REQS_FILE` build argument set to `requirements-dev.txt` e.g, 

```docker-compose build --build-arg REQS_FILE=requirements-dev.txt```

Feel free to work on any of the known issues or open a new one [here](https://github.com/cristihainic/telegram-proxy-bot/issues).