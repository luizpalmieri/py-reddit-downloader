import os
import praw
import requests
import ffmpeg
import sys
from dotenv import load_dotenv
from pathlib import Path
import logging
from typing import List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ----------------------------------------------------
# 1) Configure Reddit credentials and other settings
# ----------------------------------------------------
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
USER_AGENT = os.getenv("USER_AGENT", "my-reddit-app/0.0.1")

if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
    raise ValueError("Missing required Reddit credentials in environment variables")

# Subreddit and number of posts
SUBREDDIT_NAME = os.getenv("SUBREDDIT_NAME", "funny")
LIMIT_POSTS = int(os.getenv("LIMIT_POSTS", "10"))  # Default to 10 posts

# Output folder for downloaded and processed videos
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output_reels")
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------
# 2) Authenticate using PRAW
# ----------------------------------------------------
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=USER_AGENT,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD
)

def fetch_trending_video_posts(subreddit_name: str, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Fetches up to 'limit' hot video posts from the given subreddit.
    Returns a list of (title, url) for video posts.
    """
    try:
        subreddit = reddit.subreddit(subreddit_name)
        video_posts = []
        processed_count = 0
        
        # Fetch more posts than needed to account for non-video posts
        for submission in subreddit.hot(limit=limit * 3):
            try:
                if submission.media and "reddit_video" in str(submission.media):
                    post_title = submission.title
                    fallback_url = submission.media["reddit_video"]["fallback_url"]
                    video_posts.append((post_title, fallback_url))
                    processed_count += 1
                    
                    if processed_count >= limit:
                        break
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {str(e)}")
                continue
        
        return video_posts
    except Exception as e:
        logger.error(f"Error fetching posts from subreddit {subreddit_name}: {str(e)}")
        return []

def download_video(video_url: str, output_path: str) -> bool:
    """
    Download the video from video_url and save it to output_path.
    Returns True if successful, False otherwise.
    """
    try:
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded video to {output_path}")
        return True
    
    except requests.RequestException as e:
        logger.error(f"Failed to download video from {video_url}: {str(e)}")
        return False
    except IOError as e:
        logger.error(f"Failed to write video to {output_path}: {str(e)}")
        return False

def get_video_dimensions(input_path: str) -> Tuple[int, int]:
    """
    Get video dimensions using ffprobe.
    Returns (width, height) tuple.
    """
    try:
        probe = ffmpeg.probe(input_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        return width, height
    except Exception as e:
        logger.error(f"Failed to get video dimensions: {str(e)}")
        return 0, 0

def convert_to_reel_format(input_path: str, output_path: str) -> bool:
    """
    Convert the input video to a 9:16 aspect ratio using ffmpeg.
    Returns True if successful, False otherwise.
    """
    try:
        # Get video dimensions
        width, height = get_video_dimensions(input_path)
        if width == 0 or height == 0:
            return False

        # Calculate scaling and cropping
        target_ratio = 9/16
        current_ratio = width/height

        if current_ratio > target_ratio:  # Video is too wide
            # Scale to match target height while maintaining aspect ratio
            new_height = 1920
            new_width = int(new_height * current_ratio)
            # Then crop the sides
            crop_width = int(new_height * target_ratio)
            x_offset = (new_width - crop_width) // 2
            
            stream = (
                ffmpeg
                .input(input_path)
                .filter('scale', new_width, new_height)
                .filter('crop', crop_width, new_height, x_offset, 0)
                .output(output_path, acodec='aac', vcodec='libx264')
                .overwrite_output()
            )
        else:  # Video is too tall
            # Scale to match target width while maintaining aspect ratio
            new_width = 1080
            new_height = int(new_width / current_ratio)
            # Then crop the top and bottom
            crop_height = int(new_width / target_ratio)
            y_offset = (new_height - crop_height) // 2
            
            stream = (
                ffmpeg
                .input(input_path)
                .filter('scale', new_width, new_height)
                .filter('crop', new_width, crop_height, 0, y_offset)
                .output(output_path, acodec='aac', vcodec='libx264')
                .overwrite_output()
            )

        # Run the ffmpeg command
        stream.run(capture_stdout=True, capture_stderr=True)
        logger.info(f"Exported reel to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to convert video {input_path}: {str(e)}")
        return False

def main():
    try:
        logger.info(f"Starting to fetch {LIMIT_POSTS} videos from r/{SUBREDDIT_NAME}")
        video_posts = fetch_trending_video_posts(SUBREDDIT_NAME, LIMIT_POSTS)

        if not video_posts:
            logger.warning("No suitable video posts found.")
            return

        logger.info(f"Found {len(video_posts)} video posts")
        for idx, (title, video_url) in enumerate(video_posts, start=1):
            logger.info(f"Processing video {idx}/{len(video_posts)}: {title}")
            safe_title = "".join([c if c.isalnum() else "_" for c in title])[:100]  # Limit filename length
            download_path = Path(OUTPUT_FOLDER) / f"{safe_title}_{idx}.mp4"
            output_reel_path = Path(OUTPUT_FOLDER) / f"{safe_title}_{idx}_reel.mp4"

            if download_video(video_url, str(download_path)):
                if convert_to_reel_format(str(download_path), str(output_reel_path)):
                    try:
                        os.remove(download_path)  # Clean up original download
                    except OSError as e:
                        logger.warning(f"Failed to remove temporary file {download_path}: {str(e)}")
                        
        logger.info("Video processing completed!")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
