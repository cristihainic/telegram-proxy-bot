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
    echo "123asd-mybotkey-blabla" > secrets/bot_api_key
    ```
3. `cp .env.template .env` and modify the latter to your liking;
4. `docker-compose up` and profit.

 