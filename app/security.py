import hashlib,hmac,json,time
from urllib.parse import parse_qsl
from fastapi import HTTPException
from .config import settings
def validate_telegram_init_data(init_data:str):
    if not settings.bot_token: raise HTTPException(status_code=503,detail="Telegram bot token is not configured")
    try:
        values=dict(parse_qsl(init_data,keep_blank_values=True)); supplied=values.pop("hash"); auth_date=int(values["auth_date"])
    except (ValueError,KeyError,TypeError): raise HTTPException(status_code=401,detail="Invalid Telegram init data")
    check="\n".join(f"{k}={v}" for k,v in sorted(values.items()))
    secret=hmac.new(b"WebAppData",settings.bot_token.encode(),hashlib.sha256).digest()
    actual=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual,supplied): raise HTTPException(status_code=401,detail="Telegram signature is invalid")
    if abs(int(time.time())-auth_date)>settings.telegram_init_data_max_age: raise HTTPException(status_code=401,detail="Telegram init data has expired")
    try: user=json.loads(values["user"])
    except (KeyError,json.JSONDecodeError): raise HTTPException(status_code=401,detail="Telegram user is missing")
    if not isinstance(user.get("id"),int): raise HTTPException(status_code=401,detail="Invalid Telegram user")
    return user

def dev_user(db):
    from .models import User
    user=db.query(User).filter_by(telegram_id=900000001).first()
    if not user:
        user=User(telegram_id=900000001,username="demo_player",display_name="Пилот DROP"); db.add(user); db.commit(); db.refresh(user)
    return user
