from __future__ import annotations
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup
import pandas as pd


def create_dataframe(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """
    Given a path containing the html elements of the music league
    collect all of the data of who voted for who, as well as the
    spotify track ids for further scraping

    Parameters
    ----------
    path: Path
        the folder containing the .html files with the leagues
        results

    Returns
    -------
    tuple[pd.DataFrame, list[str]]
        the dataframe of the scraped league results, with each
        row representing a players entry in that round. A list
        of names for everyone that finished the league
    """
    data: list[dict] = []
    names: set[str] = set()

    for file in path.iterdir():
        if not file.suffix in (".htm", ".html"):
            continue

        with open(file, encoding="utf8") as f:
            html_content = f.read()

        # Load HTML content into BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        data, names = process_round(soup, data, names)

    return pd.DataFrame(data), list(names)



def process_round(soup: BeautifulSoup,
                  data: list[dict],
                  names: set[str],
    ) -> tuple[list[dict], list[str]]:
    """
    Extract the submitters, their song and the votes they received
    for each player in the round.

    Parameters
    ----------
    soup: BeautifulSoup
        the soupified html for the give round
    data: list[dict]
        the current list of data extracted from the league.
        the results from this round will be added to it.
    names: set[str]
        all current known names to have submitted a song
    """

    # Find all rows containing voters
    entries = soup.find_all(class_="card mb-4")
    round_number, round_name = get_round_details(soup)

    for entry in entries:
        submitter = (
            entry.findNext(class_="mt-3")
            .findNext("h6", class_="text-truncate")
            .text.strip("\n")
        )
        if submitter == "[Left the league]":
            continue # don't care about votes received by quitters
        names |= {submitter}
        song_id = entry["id"][len("spotify:track:") :]
        song_name = entry.find("h6", class_="card-title").text.strip()
        artist_name = entry.find("p").text.strip()
        total = int(
            entry.findNext(class_="col-auto text-end")
            .findNext("h3")
            .contents[-1]
            .text.strip()
        )
        votes = process_votes(entry, expected_total=total)
        data.append(
            {"submitter": submitter,
                "song_id": song_id,
                "song_name": song_name,
                "artist_name": artist_name,
                "round_number": round_number,
                "round": round_name,
            } | votes
        )
    return data, names

def process_votes(entry: BeautifulSoup, expected_total: int) -> dict[str, int]:
    """
    Extract the votes for this round to see who voted for who.

    Check against an expected total, telling us if the person
    didn't vote, and therefore only received downvotes if that
    rule is on in music league.

    Parameters
    ----------
    entry: BeautifulSoup
        the current submitted entry to get the votes of
    expected_total: int
        the expected total amount of points the submision
        received.

    Returns
    -------
    votes: dict[str, int]
        the number of votes each voter gave.
    """

    votes: dict[str, int] = defaultdict(int)
    for row in entry.findNext(class_="card-footer").findAll(class_="row"):
        name = row.find_next(class_="text-truncate").text

        comment = row.findAll(class_="text-break ws-pre-wrap")
        comment = comment[0].text if len(comment) else None

        score = row.findAll(class_="m-0")
        score = int(score[0].text) if len(score) else 0

        votes[name] += score

    if sum(list(votes.values())) != expected_total:
        # this means submitter didn't vote, and only received downvotes
        votes = {
            name: 0 if value > 0 else value for name, value in votes.items()
        }
    return votes


def get_round_details(soup: BeautifulSoup) -> tuple[int, str]:
    """
    Return the round number and name
    """
    round_div = soup.findAll("div", class_="card-body")[5]
    round_number = int(round_div.find(class_="text-body-tertiary").text.lstrip("ROUND "))
    round_name = round_div.find("h5", class_="card-title").text
    return round_number, round_name
