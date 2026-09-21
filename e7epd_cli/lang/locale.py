import logging
from pathlib import Path
import json
from typing import Dict, Optional
import typing

from .define import PrintTexts


class Locale:
    def __init__(self):
        self.log = logging.getLogger('e7epd.locale')
        self.path = Path(__file__).resolve().parent
        self.strings = {}       # type: Dict[str, Dict[PrintTexts, str]]
        self.lang = 'en'        # default to english

        # attempt to load all locale files
        json_file = self.path.glob("*.json")
        for j_name in json_file:
            lang = j_name.stem
            with j_name.open('r') as f:
                d = json.load(f)

            lang_cont = self.get_nested_keys(d)
            if lang_cont:
                self.strings[lang] = lang_cont      # type: ignore

        # Check the file is correct or not
        for lang in self.strings:
            for key in typing.get_args(PrintTexts):
                if key not in self.strings[lang]:
                    self.log.warning(f"Language {lang} does not contain key {key}, removing")
                    self.strings.pop(lang)
                    continue

    def get_nested_keys(self, d: dict) -> Optional[Dict[str, str]]:
        toRet: Dict[str, str] = {}
        for key, val in d.items():
            if not isinstance(key, str):
                return None
            if isinstance(val, dict):
                inner_items = self.get_nested_keys(val)
                if inner_items is None:
                    return None
                for inner_key, inner_val in inner_items.items():
                    toRet[key + '.' + inner_key] = inner_val
            elif isinstance(val, str):
                toRet[key] = val
            else:
                # we invalid file
                return None
        return toRet


    def set_lang(self, lang: str):
        self.lang = lang

    def get(self, key: PrintTexts) -> str:
        return self.strings[self.lang][key]