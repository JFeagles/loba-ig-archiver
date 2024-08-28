# loba-ig-archiver
Simple script to download and send a users instagram story to a telegram group

## Config
These env vars will need to be set to run this program:
```python
class Config(BaseSettings):
    IG_USER: str # Instagram username of the logged in account.
    IG_SESSION: str # Instagram session login file path.
    IG_PROFILE: str # Instagram profile to download stories from.
    BOT_TOKEN: str # Telegram bot token.
    TG_CHANNEL_ID: str # Telegram channel id.
```
## Warnings
- We need a instagram login to see a users stories (as is in instagram).
- Don't use an instagram account you are not willing to lose, it may be blocked due to automated behavior.
- The session file is created with instaloader, with command: `instaloader --login IG_USER` see: [instaloader docs](https://instaloader.github.io/)
