from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

# Function to download or stream video
def download_video(url: str):
    # yt-dlp options to control download quality and location
    ydl_opts = {
        'format': 'best',  # Best quality download
        'outtmpl': '/tmp/%(title)s.%(ext)s',  # Temporary save path for Vercel
        'noplaylist': True,  # Do not download playlists
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)  # Only fetch video info
            if 'url' in info_dict:
                return info_dict['url']  # Return stream URL
            else:
                raise HTTPException(status_code=404, detail="Video URL not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error in video download: " + str(e))

# API endpoint to download or stream video
@app.get("/download/")
async def download_video_api(url: str):
    download_link = download_video(url)
    return {"download_url": download_link}
