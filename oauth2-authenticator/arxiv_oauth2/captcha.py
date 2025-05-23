"""arXiv stateless captcha."""
from typing import Optional
import io
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
import logging
from .alnum_voice.alnum2mp3 import alnum_to_mp3

from starlette.responses import StreamingResponse

from . import stateless_captcha, get_client_host

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/captcha", tags=["metadata"])

class CaptchaTokenReplyModel(BaseModel):
    token: str



def generate_captcha_image(token: str, secret: str, ip_address: str, font: Optional[str] = None) -> io.BytesIO | None:
    """Provide the image for stateless captcha."""
    if not token:
        return None
    try:
        image = stateless_captcha.render(token, secret, ip_address, font=font)
    except stateless_captcha.InvalidCaptchaToken as _e:
        return None
    return image


@router.get('/image', responses = {
    200: { "content": {"image/png": {}}}
})
async def get_captcha_image(
        request: Request,
        token: str,
    ) -> StreamingResponse:
    app = request.app
    secret = app.extra['CAPTCHA_SECRET']
    font = app.extra.get('CAPTCHA_FONT')
    host = get_client_host(request)
    if host is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Host IP is not known")
    logger.info("Image captcha: host %s %s", host, token)
    try:
        image = generate_captcha_image(token, secret, host, font=font)
    except stateless_captcha.InvalidCaptchaToken as _e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(_e))

    if image is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return StreamingResponse(image,
        media_type="image/png",
        headers={
            "X-Captcha-Token": token,
            "Cache-Control": "no-store, must-revalidate",
        })

@router.get("/token")
def get_captcha_token(request: Request) -> CaptchaTokenReplyModel:
    captcha_secret = request.app.extra['CAPTCHA_SECRET']
    host = get_client_host(request)
    if host is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Host IP is not known")
    captcha_token = stateless_captcha.new(captcha_secret, host)
    logger.info("Captcha: host %s %s", host, captcha_token)
    return CaptchaTokenReplyModel(token=captcha_token)


@router.get('/audio', responses = {
    200: { "content": {"audio/mpeg": {}}}
})
async def get_captcha_audio(
        request: Request,
        token: str,
    ) -> StreamingResponse:
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No token")
    app = request.app
    secret = app.extra['CAPTCHA_SECRET']
    host = get_client_host(request)
    if host is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Host IP is not known")
    logger.info("Audio captcha: host %s %s", host, token)
    try:
        value = stateless_captcha.unpack(token, secret, host)
    except stateless_captcha.InvalidCaptchaToken as _e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(_e))
    voice = alnum_to_mp3(value)
    return StreamingResponse(voice,
        media_type="audio/mpeg",
        headers={
            "X-Captcha-Token": token,
            "Cache-Control": "no-store, must-revalidate",
        })
