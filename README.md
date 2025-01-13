# Reddit Video Downloader CLI App

A Python script that downloads videos from Reddit and converts them to vertical format suitable for Reels/Shorts (9:16 aspect ratio).

## Features

- Download videos from any subreddit
- Convert videos to 9:16 aspect ratio (1080x1920)
- Support for Reddit API authentication
- Automatic cleanup of temporary files
- Comprehensive error handling and logging

## Prerequisites

- Python 3.13 or higher
- FFmpeg installed and available in your system PATH
- Reddit API credentials (client ID, client secret, username, password)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/luizpalmieri/reddit-video-downloader.git
cd reddit-video-downloader
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.sample` to `.env` and fill in your Reddit API credentials:
```bash
cp .env.sample .env
```

## Configuration

Edit the `.env` file with your Reddit API credentials and preferences:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
USER_AGENT=my-reddit-app/0.0.1
SUBREDDIT_NAME=funny
LIMIT_POSTS=5
OUTPUT_FOLDER=output_reels
```

To get Reddit API credentials:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the required information
4. Once created, you'll get the client ID and client secret

## Usage

Run the script:
```bash
python download-reddit.py
```

The script will:
1. Fetch the most recent video posts from the specified subreddit
2. Download each video
3. Convert them to vertical format (9:16 aspect ratio)
4. Save the processed videos in the output folder

## Output

Processed videos will be saved in the `output_reels` directory (or the directory specified in `OUTPUT_FOLDER`). Each video filename will be based on the Reddit post title, with spaces and special characters replaced by underscores.

## Dependencies

- praw: Reddit API wrapper
- requests: HTTP library
- python-dotenv: Environment variable management
- ffmpeg-python: FFmpeg Python bindings

## License

This project is licensed under the MIT License - see the LICENSE file for details.
