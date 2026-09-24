"""Content identity shared by build and install stages."""
import hashlib


def digest(data):
    return hashlib.sha256(data).hexdigest()
