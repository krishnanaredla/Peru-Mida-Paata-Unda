import requests
import yaml
import logging
import sys
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, List, Optional, Union
import argparse
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Error(Exception):
    pass


class TSException(Error):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class TSLogger(Logger):
    def __init__(
        self,
        log_file=None,
        log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        *args,
        **kwargs
    ):
        self.formatter = logging.Formatter(log_format)
        self.log_file = log_file

        Logger.__init__(self, *args, **kwargs)

        self.addHandler(self.get_console_handler())
        if log_file:
            self.addHandler(self.get_file_handler())
        self.propagate = False

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(self.log_file, when="midnight")
        file_handler.setFormatter(self.formatter)
        return file_handler


logger = TSLogger(name="TSlogger")


def getConfig(path: str = "config.yaml"):
    if not path:
        path = "config.yaml"
    try:
        with open(path) as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            return data
    except Exception as e:
        logger.error("Failed to load config file :{}".format(e))
        raise TSException("Failed to load config file :{}".format(e))


def getTeluguWords(word: str, config: Dict) -> str:
    try:
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com",
            "X-RapidAPI-Key": config["translator"]["key"],
        }
        querystring = {
            "to": "te",
            "api-version": "3.0",
            "profanityAction": "NoAction",
            "textType": "plain",
        }
        payload = [{"Text": word}]
        response = requests.request(
            "POST",
            config["translator"]["url"],
            json=payload,
            headers=headers,
            params=querystring,
            verify=False,
        )
        return response.json()[0]["translations"][0]["text"]
    except Exception as e:
        logger.error("Failed to get telugu translation :{}".format(e))
        raise TSException("Failed to get telugu translation :{}".format(e))


def getSongs(word: str, config) -> List[Dict[str, str]]:
    try:
        tWord = getTeluguWords(word, config)
        req = requests.get(
            config["musixmatch"]["search_url"],
            params={
                "apikey": config["musixmatch"]["key"],
                "q": tWord,
                "f_lyrics_language": "te",
            },
        )
        data = req.json()
        tracks = []
        if not data["message"]["body"]["track_list"]:
            return [
                {
                    "Song": "Couldn't find any songs with word {}".format(word),
                    "Album": None,
                }
            ]
        for track in data["message"]["body"]["track_list"]:
            tracks.append(
                {
                    "Song": track["track"]["track_name"],
                    "Album": track["track"]["album_name"],
                }
            )
        return tracks
    except Exception as e:
        logger.error("Failed to get telugu tracks :{}".format(e))
        raise TSException("Failed to get telugu tracks :{}".format(e))


parser = argparse.ArgumentParser(description="Get Telugu songs by word")
parser.add_argument(
    "--config", "-c", help="config file location", default="config.yaml"
)
parser.add_argument("--name", "-n", help="name to search")
args = parser.parse_args()

if __name__ == "__main__":
    config = getConfig(args.config)
    tracks = getSongs(args.name, config)
    logger.info("Tracks : {}".format(tracks))
    df = pd.DataFrame(tracks)
    df = df.drop_duplicates(subset=["Song"], keep="first")[
        ~df["Album"].str.contains("Hits")
    ]
    print(df.to_string(index=False))
