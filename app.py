import dateutil.parser as parser
import feedparser
import pytz
from dateutil.tz import tzutc
from flask import Flask, render_template, request

app = Flask(__name__)


def generate_markdown_content(selected_feeds, start_date, end_date):
    # Convert the date range strings to datetime objects
    utc = pytz.UTC
    start_date = parser.parse(start_date, ignoretz=False)
    end_date = parser.parse(end_date, ignoretz=False)

    # Make datetime objects timezone-aware if they are not
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=tzutc())
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=tzutc())

    content = []

    def process_feed(feed_url):
        nonlocal content
        noop_flag = False
        feed = feedparser.parse(feed_url)
        feed_title = feed.feed.title
        content.append(f"# {feed_title}\n\n")

        for entry in feed.entries:
            entry_date_str = entry.get("published", entry.get("updated", None))
            if entry_date_str is None:
                print(f"Skipping entry with missing date: {entry.title}")
                content.append(f"Skipping entry with missing date: {entry.title}\n\n")
                continue

            entry_date = parser.parse(entry_date_str, ignoretz=True).replace(tzinfo=utc)

            if start_date <= entry_date <= end_date:
                content.append(f"## [{entry.title}]({entry.link})\n\n")

                entry_description = entry.get("description", None)
                content_encoded = entry.get("content", [{}])[0].get("value", None)

                # Use content_encoded if it exists, otherwise fall back to entry_description
                entry_content = content_encoded or entry_description

                print(f"Description for {entry.title}: {entry_content}")
                content.append(f"{entry_content}\n\n")
            else:
                noop_flag = True

        if noop_flag:
            content.append("No updates for this time frame\n\n")

    for feed_url in selected_feeds:
        process_feed(feed_url)
    print("content:\n", content)
    return "".join(content)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    # Get the form data
    selected_feeds = request.form.getlist("feed")
    date_range = request.form["daterange"]
    start_date, end_date = [
        date.strip() for date in date_range.split(" - ", 1)
    ]  # Correctly split the date range input

    # Generate the Markdown content based on the selected feeds and date range
    markdown_content = generate_markdown_content(selected_feeds, start_date, end_date)

    return markdown_content


if __name__ == "__main__":
    app.run(debug=True)
