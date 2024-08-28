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
directory_path = 'stories'


class Config(BaseSettings):
    IG_USER: str
    IG_SESSION: str
    IG_PROFILE: str
    BOT_TOKEN: str
    TG_CHANNEL_ID: str


def extract_datetime(video_filename: str) -> datetime:
    datetime_str = video_filename.split("/")[1].split("_UTC")[0]
    return datetime.strptime(datetime_str, "%Y-%m-%d_%H-%M-%S")


def organize_stories(files: List[str]) -> Dict[str, Dict]:
    stories: Dict[str, Dict] = {}
    for f in files:
        story_name, story_type = f.split(".")[:2]
        if story_name not in stories.keys():
            stories[story_name] = {}

        stories[story_name][story_type] = f"{directory_path}/{f}"

    return stories


def organize_media_to_upload(stories: Dict[str, Dict]) -> List[str]:
    media_to_upload = []
    for _, data in stories.items():
        if data.get("mp4"):
            media_to_upload.append(data["mp4"])
        elif data.get("jpg"):
            media_to_upload.append(data["jpg"])

    sorted_videos = sorted(media_to_upload, key=extract_datetime)
    return sorted_videos


@retry(stop=stop_after_attempt(5))
async def send_media(bot, channel_id: str, story_file: str):
    file_ = open(f"/tmp/{story_file}", "rb")
    if "mp4" in story_file:
        await bot.send_video(
            chat_id=channel_id, video=file_
        )
    elif "jpg" in story_file:
        await bot.send_photo(
            chat_id=channel_id, photo=file_
        )
    file_.close()


async def main():
    # Parse Config
    logging.info("Starting...")
    config = Config(**{})
    current_directory = os.getcwd()

    # Login
    logging.info("Logging in...")
    ig = Instaloader()
    ig.load_session_from_file(config.IG_USER, config.IG_SESSION)
    logging.info(f"Logged in as {config.IG_USER}")

    # Download stories
    logging.info("Downloading stories...")
    profiles = [Profile.from_username(ig.context, config.IG_PROFILE)]
    os.chdir("/tmp/")
    ig.download_stories(profiles, filename_target=directory_path)
    os.chdir(current_directory)

    # Get files
    files = os.listdir(f"/tmp/{directory_path}")
    stories = organize_stories(files)
    media_to_upload = organize_media_to_upload(stories)

    # Telegram
    bot = telegram.Bot(token=config.BOT_TOKEN)

    for story_file in media_to_upload:
        logging.info(f"Sending {story_file}...")
        await send_media(bot, config.TG_CHANNEL_ID, story_file)

    # Cleanup
    shutil.rmtree(f"/tmp/{directory_path}")


if __name__ == "__main__":
    asyncio.run(main())


def handler(event, context):
    asyncio.run(main())
    return {"statusCode": 200, "body": "Function executed successfully"}
