#########################################
# Imports
#########################################
import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from supabase import create_client, Client

#########################################
# Environment Configuration
#########################################
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_API_KEY: str = os.environ.get("SUPABASE_API_KEY")

#########################################
# Logging Configuration
#########################################
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#########################################
# Supabase Client Initialization
#########################################
if not SUPABASE_URL or not SUPABASE_API_KEY:
    logger.error("SUPABASE_URL or SUPABASE_API_KEY not found in .env file. Supabase interactions will be skipped.")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    logger.info("Supabase client initialized.")

#########################################
# FastAPI App Initialization
#########################################
app = FastAPI()

#########################################
# Constants
#########################################
PIXEL_URL = "https://shemeka-bucket.s3.ap-south-1.amazonaws.com/mail_pxl.gif"

#########################################
# Tracking Pixel Endpoint
#########################################
@app.get("/pxl.gif")
async def pxl_gif(request: Request, mic: Optional[str] = None):
    """
    Serves a 1x1 tracking pixel and updates email event data in Supabase.
    """
    # Headers to prevent caching
    no_cache_headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    # Fetch the pixel content
    try:
        async with httpx.AsyncClient() as client:
            pixel_response = await client.get(PIXEL_URL)
            pixel_response.raise_for_status()  # Raise an exception for bad status codes
            pixel_content = pixel_response.content
    except httpx.RequestError as e:
        logger.error(f"Error fetching pixel from {PIXEL_URL}: {e}")
        # Fallback: return a minimal transparent GIF if the actual pixel can't be fetched
        # This is a 1x1 transparent GIF base64 encoded
        pixel_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        no_cache_headers["Content-Type"] = "image/gif" # Ensure correct content type for fallback
    except Exception as e:
        logger.error(f"Unexpected error during pixel fetch: {e}")
        pixel_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        no_cache_headers["Content-Type"] = "image/gif"

    # Process MIC and update Supabase
    if mic and supabase:
        try:
            # Fetch current data to check for nulls and increment open_count
            response = await supabase.table('email_events').select('*').eq('mic', mic).execute()
            data = response.data

            if data:
                current_event = data[0]
                update_payload = {}
                current_timestamp = datetime.now(timezone.utc).isoformat()

                # Set first_opened_at if it's null
                if current_event.get('first_opened_at') is None:
                    update_payload['first_opened_at'] = current_timestamp

                # Increment open_count
                update_payload['open_count'] = current_event.get('open_count', 0) + 1

                # Set ip_address if it was previously null
                if current_event.get('ip_address') is None:
                    update_payload['ip_address'] = request.client.host

                # Set user_agent if it was previously null
                if current_event.get('user_agent') is None:
                    update_payload['user_agent'] = request.headers.get("User-Agent")

                if update_payload:
                    await supabase.table('email_events').update(update_payload).eq('mic', mic).execute()
                    logger.info(f"Supabase updated for MIC: {mic}")
                else:
                    logger.info(f"No new data to update for MIC: {mic}")
            else:
                logger.warning(f"MIC '{mic}' not found in email_events table. Skipping Supabase update.")
        except Exception as e:
            logger.error(f"Error interacting with Supabase for MIC '{mic}': {e}")
    elif not mic:
        logger.warning("Missing or empty 'mic' parameter. Skipping Supabase logic.")
    elif not supabase:
        logger.warning("Supabase client not initialized due to missing environment variables. Skipping Supabase logic.")

    return Response(content=pixel_content, media_type="image/gif", headers=no_cache_headers)
