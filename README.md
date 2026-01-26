# robort bot

The Robort bot is a discord bot using discordpy that summarizes League of Legends patch notes and archives pins to a dedicated channel when per channel pin limits are exceeded.

## running

```bash
pip install -r requirements.txt
python main.py
```

## Using

Set a channel for either functionality using "robort set patch notes" or "robort set pin channel". For the patch notes, every time a league patch is released the bot will send a summary (removes clutter like skins that you get when following LoL's own #game-news).

For pins, after the pin archive is set, if a message is pinned and it exceeds the limit (50) it will be moved to the pin archive automatically. Channels that already have 50 pins will need to have 1 pin moved manually and then the bot will start working. Never be unable to pin something again!
