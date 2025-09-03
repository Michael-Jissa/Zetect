# openai_test.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# load the right env file
load_dotenv("zetect.env")

def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Check zetect.env file and path.")

    client = OpenAI(api_key=api_key)

    # use the Responses API (stable in the current SDKs)
    resp = client.responses.create(
        model="gpt-4o-mini",
        input="Reply with the word OK if you can read this."
    )

    # extract plain text
    out = resp.output[0].content[0].text
    print("OpenAI says:", out)

if __name__ == "__main__":
    test_openai()
