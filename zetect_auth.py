import msal, requests, sys

CLIENT_ID = "0c60d083-5388-427f-85ce-de767ac8b818"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["User.Read", "Mail.Read"]

def main():
    app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print("Failed to create device flow:", flow)
        sys.exit(1)

    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        print("✅ Signed in.")
        
        r = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {result['access_token']}"}
        )
        print("Me:", r.json())
    else:
        print("❌ Auth failed:", result.get("error"), result.get("error_description"))

if __name__ == "__main__":
    main()
