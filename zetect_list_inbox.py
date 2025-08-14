import msal, requests, sys, os

CLIENT_ID = "0c60d083-5388-427f-85ce-de767ac8b818"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["User.Read", "Mail.Read"]
CACHE_FILE = "token_cache.bin"

def load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache

def save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())

def get_token(app, cache):
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            print("Failed to create device flow:", flow)
            sys.exit(1)
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
        save_cache(cache)
    return result

def main():
    cache = load_cache()
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    token = get_token(app, cache)
    if "access_token" not in token:
        print("Auth failed:", token)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token['access_token']}"}
    url = ("https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
           "?$select=sender,subject,receivedDateTime&$top=5")
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("Graph error:", r.status_code, r.text)
        sys.exit(1)

    for i, m in enumerate(r.json().get("value", []), 1):
        sender = m.get("sender", {}).get("emailAddress", {}).get("address", "(unknown)")
        print(f"{i}. {m.get('subject', '(no subject)')}  — {sender} — {m.get('receivedDateTime')}")

if __name__ == "__main__":
    main()
