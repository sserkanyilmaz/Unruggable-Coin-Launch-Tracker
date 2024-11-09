# Starknet Memecoin Launch Tracker

A real-time monitoring bot that tracks new memecoin deployments on the Starknet blockchain and sends instant notifications via Telegram.

## Features

- Real-time monitoring of new memecoin deployments
- Instant Telegram notifications
- Block-specific checking capability
- User subscription management
- Easy-to-use command interface

## Commands

- `/start` - Initialize the bot and get usage instructions
- `/subscribe` - Subscribe to memecoin deployment notifications
- `/unsubscribe` - Unsubscribe from notifications
- `/check <block_hash>` - Check a specific block for memecoin deployments

## Setup

1. Clone the repository:
    ```bash
        git clone https://github.com/sserkanyilmaz/UnRugged-Coin-Launch-Tracker.git
    ```

2. Install required dependencies:
    ```bash
        pip install python-telegram-bot requests asyncio
    ```

3. Configure the bot:
   - Create a Telegram bot and get your BOT_TOKEN from [@BotFather](https://t.me/botfather)
   - Get your Starknet API key from [Blast API](https://blastapi.io/)
   - Update the following constants in `tracker.py`:
     - `BOT_TOKEN`
     - `API_URL`

4. Run the bot:
    ```bash
        python tracker.py
    ```

## Requirements

- Python 3.7+
- python-telegram-bot
- requests
- asyncio

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational purposes only. Always do your own research before investing in any cryptocurrency.
