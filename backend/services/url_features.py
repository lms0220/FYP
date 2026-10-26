"""URL normalisation shared by model training and inference."""

import re


def normalize_url_for_model(url):
    """Drop scheme, leading www. and surrounding noise.

    The training CSV mixes bare hosts and scheme-prefixed URLs unevenly across
    classes, so the model otherwise learns "https://" as a malicious signal.
    """
    url = url.strip().lower()
    url = re.sub(r"^[a-z][a-z0-9+.-]*://", "", url)
    url = re.sub(r"^www\d*\.", "", url)
    return url.rstrip("/")


def host_of(normalized):
    return re.split(r"[/?#]", normalized, maxsplit=1)[0].split(":")[0]
