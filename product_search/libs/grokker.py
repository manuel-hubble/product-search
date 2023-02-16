from __future__ import annotations

import datetime
import json
import logging
import os
import re
from contextlib import nullcontext
from pathlib import Path

import json_stream

from .cpe import Part

OS_STRING_SPECIAL_CHARACTERS: str = r"[_,:.)(\\]"


def grok_cpe_file(input_file: str = "/tmp/product_search/cpe-match-strings.json",
                  synonyms_file: str = "./cpe_name_os_synonyms.json", part=Part.OPERATING_SYSTEM,
                  destination_dir="/tmp/product_search") -> dict[str, list[list[str]]]:
    """

    :param input_file:
    :param synonyms_file:
    :param part:
    :param destination_dir:
    :return:
    """
    if not (input_file and Path(input_file).is_file()):
        raise FileNotFoundError(f"\"{input_file}\" is not a valid file")

    with open(input_file) as f:
        cpe_data = json_stream.load(f)

        if not cpe_data:
            raise ValueError(f"Could not load CPE data from file at \"{input_file}\"")

        synonyms_data: dict = {}
        try:
            with open(synonyms_file, 'r') as sf:
                synonyms_data = json.load(sf)
        except (IOError, OSError):
            logging.info(f"Synonym file \"{synonyms_file}\" does not exist or cannot be read.")
        except Exception as e:
            logging.warning(f"Synonym file \"{synonyms_file}\" does not have the correct format.", e)

        result: dict = {}

        for entry in cpe_data:
            """
            Will yield entries of the form:
                {"cpe_name": "cpe:2.3:o:canonical:ubuntu_linux:14.04.1:*:*:*:*:*:*:*", 
                "title": "Canonical Ubuntu Linux 14.04.1"}
            As lists like:
                [["canonical", None], ["ubuntu"], ["linux", None], ["14"], ["04"], ["1"]]
            """
            cpe_name: str = entry.get("cpe_name")
            title: str = entry.get("title")
            if cpe_name:
                transformed_cpe_name: list[list[str]] = transform_cpe_name(cpe_name, synonyms_data, part)
                result[title] = transformed_cpe_name

        if destination_dir:
            os.makedirs(destination_dir, exist_ok=True)
            now: str = datetime.datetime.now().isoformat(timespec='milliseconds')
            destination_file: str = os.path.join(destination_dir, f"{now}-{str(part)}-cpe-grokked-strings.json")
            with (open(destination_file, "w") if destination_file else nullcontext()) as of:
                os.makedirs(destination_dir, exist_ok=True)
                if of:
                    of.write(json.dumps(result, indent=4, sort_keys=True))

    return result


def transform_cpe_name(cpe_name: str, synonyms_data: dict = None, part=Part.OPERATING_SYSTEM) -> list[list[str | None]]:
    """

    :param cpe_name:
    :param synonyms_data:
    :param part:
    :return:
    """
    if not (cpe_name and "cpe:2.3:" in cpe_name):
        return []

    cpe_name_fields: list[str] = list(
        filter(lambda x: x not in ["*", "-", ""],
               re.split(OS_STRING_SPECIAL_CHARACTERS, cpe_name.removeprefix("cpe:2.3:" + part.to_code() + ":"))))

    transformed_cpe_name: list[list[str]] = []
    for index, component in enumerate(cpe_name_fields):
        component_lower: str = component.lower()
        component_list: list[str | None] = [component_lower]
        if index == 0:
            # Assume this is the vendor. Add an extra None, as most identification strings come without a vendor name.
            # This is needed to skip the field during the construction of the trie.
            component_list.append(None)

        # Add synonyms, if any.
        if synonyms_data:
            synonyms: list[str] = synonyms_data.get(component_lower)
            if synonyms:
                # TODO: re-run this to add synonyms of synonyms, until no more are found.
                component_list.extend([synonym.lower() if synonym else None for synonym in synonyms])

        transformed_cpe_name.append(component_list)

    return transformed_cpe_name
