from hmac import new
from json import loads
from os import urandom
from typing import Union
from hashlib import sha1
from base64 import b64decode, b64encode

DEVKEY = 'e7309ecc0953c6fa60005b2765f99dbbc965c8e9'
SIGKEY = 'dfa5ed192dda6e88a12fe12130dc6206b1251e44'
PREFIX = "19"


def generate_device(data: bytes = None) -> str:
    """
    Generate a device ID using the provided data or random bytes.
    """
    if isinstance(data, str):
        data = bytes(data, 'utf-8')
    identifier = PREFIX + (data or urandom(20))
    mac = new(DEVICE_KEY, identifier, sha1)
    return f"{identifier.hex()}{mac.hexdigest()}".upper()

def generate_signature(data: Union[str, bytes]) -> str:
    """
    Generate a signature for the given data.
    """
    data = data if isinstance(data, bytes) else data.encode("utf-8")
    return b64encode(PREFIX + new(SIG_KEY, data, sha1).digest()).decode("utf-8")

def update_deviceId(device: str) -> str:
    """
    Update a device ID using its hexadecimal representation.
    """
    return gen_deviceId(bytes.fromhex(device[2:42]))

def self_deviceId(login: str) -> str:
    """
    Generate a device ID using the SHA1 hash of an login.
    """
    return gen_deviceId(sha1(login.encode()).digest())

def decode_sid(sid: str) -> dict:
    """
    Decode a SID into a dictionary.
    """
    sid = sid.replace("-", "+").replace("_", "/")
    sid += "=" * (-len(sid) % 4)
    decoded_bytes = b64decode(sid.encode())
    return loads(decoded_bytes[1:-20].decode())

def sid_to_uid(SID: str) -> str:
    """
    Extract the user ID from a decoded SID.
    """
    return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str:
    """
    Extract the IP address from a decoded SID.
    """
    return decode_sid(SID)["4"]
