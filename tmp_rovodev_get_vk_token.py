#!/usr/bin/env python3
"""
Helper to obtain VK user access token via VK ID (Authorization Code Flow + PKCE).

Steps it performs:
1) Ask for APP_ID (client_id) and optional redirect_uri (default: https://oauth.vk.com/blank.html)
2) Generate PKCE code_verifier and code_challenge
3) Print ready authorization URL to open in a browser
4) Ask you to paste the `code` from the redirect URL
5) Exchange code for tokens at id.vk.com (fallback id.vk.ru)

Outputs:
- access_token (vk2.a...)
- refresh_token
- expires_in, user_id, scope

Note:
- Ensure your VK Website app has the redirect_uri whitelisted exactly
  (e.g., https://oauth.vk.com/blank.html) in the app settings.
- Scopes used: video wall groups offline
- Do not share the printed tokens publicly.
"""

import base64
import hashlib
import json
import string
import secrets
import sys
import urllib.parse
import urllib.request
from typing import Tuple

DEFAULT_REDIRECT_URI = "https://oauth.vk.com/blank.html"
DEFAULT_SCOPES = ["video", "wall", "groups", "offline"]
AUTH_HOSTS = ["id.vk.com", "id.vk.ru"]  # try .com first, then .ru

OAUTH_VK_COM_AUTH = "https://oauth.vk.com/authorize"
OAUTH_VK_COM_TOKEN = "https://oauth.vk.com/access_token"


def generate_code_verifier(length: int = 64) -> str:
    # RFC 7636 allowed chars: ALPHA / DIGIT / "-" / "." / "_" / "~"
    allowed = string.ascii_letters + string.digits + "-._~"
    return "".join(secrets.choice(allowed) for _ in range(length))


def base64url_no_pad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64url_no_pad(digest)


def build_auth_url(app_id: str, redirect_uri: str, code_challenge: str, scopes=DEFAULT_SCOPES, state: str = "rovodev") -> Tuple[str, str, str]:
    params_id = {
        "client_id": app_id,
        "display": "page",
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),  # space-separated (VK ID ignores VK API scopes)
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    url_id_com = f"https://{AUTH_HOSTS[0]}/authorize?" + urllib.parse.urlencode(params_id, safe=":/")
    url_id_ru = f"https://{AUTH_HOSTS[1]}/authorize?" + urllib.parse.urlencode(params_id, safe=":/")

    # classic oauth.vk.com (for VK API token with video/wall/groups)
    params_oauth = {
        "client_id": app_id,
        "display": "page",
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "video,wall,groups,offline",  # comma-separated as per oauth.vk.com
        "v": "5.199",
        "revoke": 1,
        # no PKCE here for classic flow
    }
    url_oauth = OAUTH_VK_COM_AUTH + "?" + urllib.parse.urlencode(params_oauth, safe=":/")
    return url_id_com, url_id_ru, url_oauth


def post_form(url: str, data: dict, timeout: int = 20) -> Tuple[int, str]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except Exception as e:
        return -1, str(e)


def exchange_code_for_tokens(app_id: str, redirect_uri: str, code: str, code_verifier: str, device_id: str = "") -> dict:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    if device_id:
        payload["device_id"] = device_id
    # Try .com first, using /oauth2/auth as per new VK ID docs
    last_err = None
    for host in AUTH_HOSTS:
        token_url = f"https://{host}/oauth2/auth"
        status, body = post_form(token_url, payload)
        if status == 200:
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                raise RuntimeError(f"Non-JSON token response from {host}: {body[:200]}")
        else:
            # keep the last error for reporting
            last_err = f"{host} -> status={status}, body={body[:300]}"
    raise RuntimeError(f"Token exchange failed. Last error: {last_err}")


def main():
    print("VK ID OAuth2 (PKCE) helper — by Rovo Dev\n")
    app_id = input("Enter your APP_ID (client_id): ").strip()
    if not app_id:
        print("APP_ID is required.")
        sys.exit(1)

    redirect_uri = input(f"Enter redirect_uri (default {DEFAULT_REDIRECT_URI}): ").strip() or DEFAULT_REDIRECT_URI
    # basic sanity for https
    if not redirect_uri.startswith("https://"):
        print("Warning: redirect_uri should be HTTPS and must match exactly what is set in your VK app settings.")

    scopes = input(f"Enter scopes space-separated (default: {' '.join(DEFAULT_SCOPES)}): ").strip()
    if scopes:
        scopes_list = scopes.split()
    else:
        scopes_list = DEFAULT_SCOPES

    code_verifier = generate_code_verifier(64)
    code_challenge = generate_code_challenge(code_verifier)

    print("\nGenerated PKCE:")
    print("code_verifier:", code_verifier)
    print("code_challenge:", code_challenge)

    auth_url_params = {
        "client_id": app_id,
        "display": "page",
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes_list),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": "rovodev",
    }

    url_id_com, url_id_ru, url_oauth = build_auth_url(app_id, redirect_uri, code_challenge, scopes_list)

    print("\nTwo ways to authorize:")
    print("1) VK ID (id.vk.com) — returns vk2.a tokens (may not include VK API scopes):")
    print(url_id_com)
    print("   Mirror:")
    print(url_id_ru)
    print("\n2) Classic VK OAuth (oauth.vk.com) — returns VK API token with video/wall/groups/office:")
    print(url_oauth)

    print("\nOpen ONE of the URLs above, grant access, then you'll be redirected to redirect_uri with ?code=...\nCopy the 'code' value from the address bar and paste it below.\n")
    code = input("Paste the 'code' here: ").strip()
    if not code:
        print("Code is required to exchange tokens.")
        sys.exit(2)
    device_id = input("Paste device_id from the URL if present (or leave blank): ").strip()

    print("\nExchanging code for tokens...\n")
    # Decide which backend to use based on a simple heuristic: if device_id present, try VK ID first; otherwise try oauth.vk.com
    tokens = None
    try:
        if device_id:
            tokens = exchange_code_for_tokens(app_id, redirect_uri, code, code_verifier, device_id)
        else:
            # classic oauth.vk.com: requires client_secret; ask optionally
            client_secret = input("If you used oauth.vk.com URL, enter CLIENT_SECRET (or leave blank to skip): ").strip()
            if client_secret:
                # GET request
                url = (
                    OAUTH_VK_COM_TOKEN
                    + "?"
                    + urllib.parse.urlencode(
                        {
                            "client_id": app_id,
                            "client_secret": client_secret,
                            "redirect_uri": redirect_uri,
                            "code": code,
                        }
                    )
                )
                try:
                    with urllib.request.urlopen(url, timeout=20) as resp:
                        body = resp.read().decode("utf-8")
                        tokens = json.loads(body)
                except Exception as e:
                    print("Classic oauth.vk.com token exchange failed:", e)
        if not tokens:
            # Fallback to VK ID flow
            tokens = exchange_code_for_tokens(app_id, redirect_uri, code, code_verifier, device_id)
    except Exception as e:
        print("Error exchanging code for tokens:\n", e)
        sys.exit(3)

    print("Success! Token response:")
    print(json.dumps(tokens, ensure_ascii=False, indent=2))

    print("\nUsage tips:")
    print("- Set VK_ACCESS_TOKEN from the 'access_token' above.")
    print("- Keep 'refresh_token' safe; you can refresh later via grant_type=refresh_token.")
    print("- For group posting with a user token, ensure the user is an admin and use owner_id = -GROUP_ID.")


if __name__ == "__main__":
    main()
