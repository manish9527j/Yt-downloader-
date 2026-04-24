from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import yt_dlp
from typing import Optional

app = FastAPI(title="YouTube Downloader API")

# Add CORS middleware for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_video_info(url: str, format_type: Optional[str] = "best"):
    """Extract video information and streaming URL"""
    ydl_opts = {
        'format': format_type,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            if not info_dict:
                raise HTTPException(status_code=404, detail="Could not extract video information")
            
            # Get the best format URL
            formats = info_dict.get('formats', [])
            
            # Try to get the requested format or fallback to best
            video_url = info_dict.get('url')
            
            if not video_url and formats:
                # Get the best format with both video and audio
                for f in reversed(formats):
                    if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        video_url = f.get('url')
                        break
                
                # If no combined format, get the best video format
                if not video_url:
                    for f in reversed(formats):
                        if f.get('url'):
                            video_url = f.get('url')
                            break
            
            if not video_url:
                raise HTTPException(status_code=404, detail="No downloadable URL found")
            
            return {
                "title": info_dict.get('title', 'Unknown'),
                "thumbnail": info_dict.get('thumbnail'),
                "duration": info_dict.get('duration'),
                "uploader": info_dict.get('uploader'),
                "view_count": info_dict.get('view_count'),
                "download_url": video_url,
            }
            
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "YouTube Downloader API",
        "endpoints": {
            "/download": "GET - Download video (params: url, format)",
            "/info": "GET - Get video info (params: url)",
        }
    }


@app.get("/download")
async def download_video_api(
    url: str = Query(..., description="YouTube video URL"),
    format: Optional[str] = Query("best", description="Video format (best, worst, bestaudio, bestvideo)")
):
    """Get download URL for a YouTube video"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    result = get_video_info(url, format)
    return result


@app.get("/info")
async def get_video_info_api(
    url: str = Query(..., description="YouTube video URL")
):
    """Get information about a YouTube video"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    result = get_video_info(url)
    # Remove download_url for info endpoint
    result.pop("download_url", None)
    return result


# Vercel serverless handler
handler = Mangum(app, lifespan="off")
