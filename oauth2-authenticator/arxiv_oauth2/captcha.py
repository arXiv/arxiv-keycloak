"""arXiv category routes."""
from http import HTTPStatus
from typing import Optional, List
import io
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
import logging

from starlette.responses import StreamingResponse

from . import stateless_captcha, get_client_host

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/captcha", tags=["metadata"])

class CaptchaTokenReplyModel(BaseModel):
    token: str



def generate_captcha_image(token: str, secret: str, ip_address: str, font: Optional[str] = None) -> io.BytesIO:
    """Provide the image for stateless captcha."""
    if not token:
        return None
    try:
        image = stateless_captcha.render(token, secret, ip_address, font=font)
    except stateless_captcha.InvalidCaptchaToken as e:
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
    image = generate_captcha_image(token, secret, host, font=font)
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
    captcha_token = stateless_captcha.new(captcha_secret, host)
    return CaptchaTokenReplyModel(token=captcha_token)

