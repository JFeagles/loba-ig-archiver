from typing import Dict, List
from instaloader import Profile, Instaloader
import asyncio
import os
from pydantic_settings import BaseSettings
import shutil
import telegram
from datetime import datetime
import logging
from tenacity import retry
from tenacity.stop import stop_after_attempt
logging.basicConfig(level=logging.INFO)


class Config(BaseSettings):
    IG_USER: str
    IG_PASSWORD: str
    IG_PROFILE: str
    BOT_TOKEN: str
    TG_CHANNEL_ID: str


def extract_datetime(video_filename: str) -> datetime:
    datetime_str = video_filename.split('/')[1].split('_UTC')[0]
    return datetime.strptime(datetime_str, '%Y-%m-%d_%H-%M-%S')


def organize_stories(files: List[str]) -> Dict[str, Dict]:
    stories: Dict[str, Dict] = {}
    for f in files:
        story_name, story_type = f.split(".")[:2]
        if story_name not in stories.keys():
            stories[story_name] = {}

        stories[story_name][story_type] = f":stories/{f}"

    return stories


def organize_media_to_upload(stories: Dict[str, Dict]) -> List[str]:
    media_to_upload = []
    for _, data in stories.items():
        if data.get('mp4'):
            media_to_upload.append(data['mp4'])
        elif data.get('jpg'):
            media_to_upload.append(data['jpg'])

    sorted_videos = sorted(media_to_upload, key=extract_datetime)
    return sorted_videos


@retry(stop=stop_after_attempt(5))
async def send_media(bot, channel_id: str, story_file: str):
    if 'mp4' in story_file:
        await bot.send_video(
            chat_id=channel_id, video=open(story_file, 'rb')
        )
    elif 'jpg' in story_file:
        await bot.send_photo(
            chat_id=channel_id, photo=open(story_file, 'rb')
        )


async def main():

    # Parse Config
    logging.info("Starting...")
    config = Config(**{})

    # Login
    logging.info("Logging in...")
    ig = Instaloader()
    ig.login(config.IG_USER, config.IG_PASSWORD)
    logging.info(f"Logged in as {config.IG_USER}")

    # Download stories
    profiles = [Profile.from_username(ig.context, config.IG_PROFILE)]
    ig.download_stories(profiles)

    # Get files
    files = os.listdir(":stories")
    stories = organize_stories(files)
    media_to_upload = organize_media_to_upload(stories)

    # Telegram
    bot = telegram.Bot(token=config.BOT_TOKEN)

    for story_file in media_to_upload:
        logging.info(f"Sending {story_file}...")
        await send_media(bot, config.TG_CHANNEL_ID, story_file)

    # Cleanup
    shutil.rmtree(":stories")


if __name__ == "__main__":
    asyncio.run(main())
