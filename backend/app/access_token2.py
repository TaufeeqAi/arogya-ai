"""Agora AccessToken2 ("007") builder for RTC + RTM, ported from AgoraIO/Tools DynamicKey (MIT)."""
import base64
import hmac
import random
import struct
import time
import zlib
from hashlib import sha256


def _u16(x): return struct.pack("<H", int(x))
def _u32(x): return struct.pack("<I", int(x))
def _str(b: bytes): return _u16(len(b)) + b


def _map_u32(m: dict) -> bytes:
    out = _u16(len(m))
    for k in sorted(m):
        out += _u16(k) + _u32(m[k])
    return out


class _Service:
    def __init__(self, type_: int):
        self.type = type_
        self.privileges: dict[int, int] = {}

    def pack(self) -> bytes:
        return _u16(self.type) + _map_u32(self.privileges)


class ServiceRtc(_Service):
    JOIN, PUB_AUDIO, PUB_VIDEO, PUB_DATA = 1, 2, 3, 4

    def __init__(self, channel: str, uid: int):
        super().__init__(1)
        self.channel = channel.encode()
        self.uid = b"" if uid == 0 else str(uid).encode()

    def pack(self) -> bytes:
        return super().pack() + _str(self.channel) + _str(self.uid)


class ServiceRtm(_Service):
    LOGIN = 1

    def __init__(self, user_id: str):
        super().__init__(2)
        self.user_id = user_id.encode()

    def pack(self) -> bytes:
        return super().pack() + _str(self.user_id)


def build_rtc_rtm_token(app_id: str, app_cert: str, channel: str, uid: int, expire: int = 86400,
                        with_rtm: bool = True) -> str:
    issue_ts = int(time.time())
    salt = random.randint(1, 99999999)
    services = []
    rtc = ServiceRtc(channel, uid)
    for p in (ServiceRtc.JOIN, ServiceRtc.PUB_AUDIO, ServiceRtc.PUB_VIDEO, ServiceRtc.PUB_DATA):
        rtc.privileges[p] = expire
    services.append(rtc)
    if with_rtm:
        rtm = ServiceRtm(str(uid))
        rtm.privileges[ServiceRtm.LOGIN] = expire
        services.append(rtm)
    signing = hmac.new(_u32(issue_ts), app_cert.encode(), sha256).digest()
    signing = hmac.new(_u32(salt), signing, sha256).digest()
    info = _str(app_id.encode()) + _u32(issue_ts) + _u32(expire) + _u32(salt) + _u16(len(services))
    for sv in services:
        info += sv.pack()
    signature = hmac.new(signing, info, sha256).digest()
    return "007" + base64.b64encode(zlib.compress(_str(signature) + info)).decode()
