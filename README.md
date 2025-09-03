# Zetect

Zetect is an experimental email security assistant that integrates with Microsoft Outlook (via Microsoft Graph API) and OpenAI to help detect and analyze suspicious emails.

It connects to your Outlook inbox, fetches emails, and uses GPT to classify or comment on them.

> ⚠️ **Note:** For security reasons, no API keys or cached credentials are included in this repository. To run Zetect, you must set up your own Azure App registration and provide your own OpenAI API key.

---

## Features

- Authenticate with Microsoft Outlook using OAuth2 (via Microsoft Graph).
- Fetch and list recent inbox emails.
- Send email content to GPT for classification or analysis.
- Configurable and extensible for additional AI-powered workflows.

---

## Requirements

- Python 3.10+
- A registered Azure App with Microsoft Graph permissions.
- An OpenAI API key.
- A `.env` file with your credentials.

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Michael-Jissa/Zetect.git
cd Zetect
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root (e.g. `zetect.env`) with the following keys:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Microsoft Graph (from your Azure App registration)
CLIENT_ID=your_azure_client_id
CLIENT_SECRET=your_azure_client_secret
TENANT_ID=your_azure_tenant_id
REDIRECT_URI=http://localhost:8000
```

### 4. Azure App Setup

1. Go to the **Azure Portal**.
2. Register a new **App Registration**.
3. Configure API Permissions → add `Mail.Read`.
4. Generate a **Client Secret**.
5. Copy the **Client ID**, **Tenant ID**, and **Client Secret** into your `.env`.
6. Set a redirect URI (e.g., `http://localhost:8000`).

---

## Usage

### Authenticate

The first time you run Zetect, authenticate with Microsoft Graph:

```bash
zetect auth
```

You’ll be redirected to a browser window to log in to your Microsoft account.

If successful, the terminal will confirm with:

```
OpenAI says: OK
```

### Fetch and Analyze Emails

List your inbox:
```bash
zetect list inbox
```

Analyze with GPT:
```bash
zetect classify inbox
```

(Or replace `classify` with your own custom action.)

---

## Notes

- Each user must provide their own OpenAI key and Azure credentials.
- This project does **not** include cached tokens or authentication files.
- For security, never commit your `.env` file to GitHub.

---

## Roadmap

- Customizable classification logic.
- Expanded support for multiple mailboxes.
- Automated quarantining of flagged emails.

---

## License

MIT License

