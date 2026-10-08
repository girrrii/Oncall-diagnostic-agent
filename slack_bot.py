import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from agent import ask

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.event("app_mention")
def handle_mention(event, say):
    query = event["text"]
    # Strip the bot mention (e.g. "<@U12345> what's happening with checkout-service?")
    query = query.split(">", 1)[-1].strip()

    say(f"Investigating `{query}`...")
    answer = ask(query)
    say(answer)


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print("On-Call Agent is running. Mention the bot in Slack to ask a question.")
    handler.start()