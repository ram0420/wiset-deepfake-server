# app/security.py
import hmac, hashlib, time, base64, json, os

_SECRET = os.environ.get("CLEANUP_SECRET", "change-me")  # 🚨 운영에서는 환경변수로 설정!

def make_cleanup_token(keys: list[str], ttl_sec=3600) -> str:
    payload = {"keys": keys, "exp": int(time.time()) + ttl_sec}
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig = hmac.new(_SECRET.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + sig).decode()

def verify_cleanup_token(token: str):
    blob = base64.urlsafe_b64decode(token.encode())
    raw, sig = blob.rsplit(b".", 1)
    ok = hmac.compare_digest(
        hmac.new(_SECRET.encode(), raw, hashlib.sha256).digest(), sig
    )
    if not ok:
        return None
    payload = json.loads(raw)
    if payload["exp"] < int(time.time()):
        return None
    return payload
