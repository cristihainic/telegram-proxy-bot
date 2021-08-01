![build](https://github.com/cristihainic/telegram-proxy-bot/actions/workflows/tests.yml/badge.svg)

# Telegram Proxy Bot

A bot to receive messages on Telegram without revealing your identity to message senders. 

### Features
- Out-of-the-box, this bot forwards all messages it receives to a chat of your liking.
- Potentially, this Telegram bot can be extended to do whatever you want.

### Get your bot running
1. Clone this repo on the server which you want to run the bot from and `cd` into the root directory;
2. Create a `secrets` directory with a `bot_api_key` file containing your Telegram bot key:
    ```
    mkdir secrets
    printf "123asd-mybotkey-blabla" > secrets/bot_api_key
    ```
3. `cp .env.template .env` and modify the latter to your liking;
4. `docker-compose up` and profit.

### Development
Contributions are welcome! 

When developing, build the project with the `REQS_FILE` build argument set to `requirements-dev.txt` e.g, 

```docker-compose build --build-arg REQS_FILE=requirements-dev.txt```

Feel free to work on any of the known issues or open a new one [here](https://github.com/cristihainic/telegram-proxy-bot/issues).