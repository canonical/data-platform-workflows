import csv
import dataclasses
import pathlib
import re
import shutil
import requests
import yaml

NAVTABLE_START_MARKER = "[details=Navigation]"
NAVTABLE_END_MARKER = "[/details]"

def get_topic(topic_id_: str):
    """Get markdown content of a discourse.charmhub.io topic"""
    
    response = requests.get(
        f"https://discourse.charmhub.io/raw/{topic_id_}/1"
    )  # "/1" for post 1
    
    response.raise_for_status()
    return response.text


class NoTopicToDownload(Exception):
    """No Discourse topic is available to download

    Happens if:
    - no "Navlink" is provided (e.g. for a navigation group)
    - "Navlink" is an external URL
    """

@dataclasses.dataclass
class Topic:
    """Discourse topic to download"""

    id: str
    path: pathlib.Path

    @classmethod
    def from_csv_row(cls, row_: dict):
        # Example `row_`: {'Level': '2', 'Path': 't-overview', 'Navlink': '[Overview](/t/9707)'}

        # Extract Discourse topic ID from "Navlink"
        # Example `link`: "/t/9707"
        link = re.fullmatch(r"\[.*?]\((.*?)\)", row_["Navlink"]).group(1)
        if link == "":
            raise NoTopicToDownload
        elif link.startswith("http") and "discourse.charmhub.io" not in link:
            # Ignore external links (e.g. "https://canonical.com/data/docs/postgresql/iaas")
            raise NoTopicToDownload

        match = re.fullmatch(r"/t/([0-9]+)", link)
        if not match:
            raise ValueError(
                f'Invalid navlink "{link}". Expected something like "/t/9707"'
            )
        # Example `topic_id`: "9707"
        topic_id = match.group(1)

        # Determine local path to download Markdown file
        # Example `topic_slug`: "t-overview"
        topic_slug = row_["Path"]
        diataxis_directory = {
            "t-": "tutorial",
            "h-": "how-to",
            "r-": "reference",
            "e-": "explanation",
        }[topic_slug[:2]]

        # Example `path`: "docs/tutorial/t-overview.md"
        path = pathlib.Path("docs/") / diataxis_directory / f"{topic_slug}.md"

        return cls(topic_id, path)

def main():
    """Download Discourse documentation topics to docs/ directory"""
    
    # Example `overview_topic_link`: "https://discourse.charmhub.io/t/charmed-postgresql-documentation/9710"
    overview_topic_link: str = yaml.safe_load(pathlib.Path("metadata.yaml").read_text())["docs"]
    assert overview_topic_link.startswith("https://discourse.charmhub.io/")

    # Example `topic_id`: "9710"
    topic_id = overview_topic_link.split("/")[-1]
    overview_topic_markdown = get_topic(topic_id)

    # Example of an expected markdown table:
    # | Level | Path | Navlink |
    # |--------|--------|-------------|
    # | 1 | tutorial | [Tutorial]() |
    # | 2 | t-overview | [Overview](/t/9707) |
    # | 2 | t-set-up | [1. Set up the environment](/t/9709) |
    # | 2 | t-deploy | [2. Deploy PostgreSQL](/t/9697) |
    # | 1 | search | [Search](https://canonical.com/data/docs/postgresql/iaas) |

    # Search for table delimiters NAVTABLE_START_MARKER and NAVTABLE_END_MARKER
    start_index = overview_topic_markdown.find(NAVTABLE_START_MARKER)
    if start_index == -1:
        raise ValueError("Could not find Navtable start marker " + NAVTABLE_START_MARKER + " in the overview topic") 

    end_index = overview_topic_markdown.find(NAVTABLE_END_MARKER)
    if end_index == -1:
        raise ValueError("Could not find Navtable end marker " + NAVTABLE_END_MARKER + " in the overview topic")

    start_index += len(NAVTABLE_START_MARKER)
    end_index = overview_topic_markdown.find(NAVTABLE_END_MARKER, start_index)

    table_raw = overview_topic_markdown[start_index:end_index].strip() # remove leading and trailing whitespace
    if table_raw == "":
        raise ValueError("Could not find a valid table")

    # Convert Markdown table to list[dict[str, str]]
    # (https://stackoverflow.com/a/78254495)
    rows: list[dict] = list(csv.DictReader(table_raw.split("\n"), delimiter="|"))
    # Remove first row (e.g. "|--------|--------|-------------|")
    rows = rows[2:]
    rows: list[dict[str, str]] = [
        {key.strip(): value.strip() for key, value in row.items() if key != ''}
        for row in rows
    ]
    shutil.rmtree(pathlib.Path("docs/"))
    
    for row in rows:
        # Example `row`: {'Level': '2', 'Path': 't-overview', 'Navlink': '[Overview](/t/9707)'} 
        try:
            topic = Topic.from_csv_row(row)
        except NoTopicToDownload:
            continue
        
        # Download topic markdown to `topic.path`
        topic.path.parent.mkdir(parents=True, exist_ok=True)
        topic.path.write_text(get_topic(topic_id))