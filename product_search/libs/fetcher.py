from __future__ import annotations

import datetime
import json
import logging
import os
import time
from urllib.parse import urlencode

import httpx
from httpx import Response

from .cpe import Part


class FetchError(Exception):
    pass


def fetch_from_nvd_api(url: str = "https://services.nvd.nist.gov/rest/json/cpes/2.0",
                       api_key: str = "c5193f7f-6d4c-4634-a671-77ecdcd8b49c",
                       part: Part = Part.OPERATING_SYSTEM,
                       vendor: str = "",
                       cutoff: str = "1970-01-01T00:00:00.000",
                       exclude_keywords: list[str] = ["firmware"],
                       destination_dir: str = "/tmp/product_search",
                       pause: float = 6
                       ) -> str:
    """
    Fetch CPE strings using the NVD API, and store them locally.
    Will filter out deprecated CPEs.
    :param url:
    :param api_key:
    :param part:
    :param vendor:
    :param cutoff:
    :param exclude_keywords:
    :param destination_dir:
    :param pause
    :return:
    """
    os.makedirs(destination_dir, exist_ok=True)

    now: str = datetime.datetime.now().isoformat(timespec='milliseconds')
    destination_file: str = os.path.join(destination_dir, f"{now}-{str(part)}-cpe-match-strings.json")

    tries = 5
    start_index = 0
    query_dict: dict = {"cpeMatchString": "cpe:2.3:" + part.to_code() + ((":" + vendor) if vendor else ""),
                        "resultsPerPage": 100, "startIndex": start_index}

    with open(destination_file, "w") as f:
        headers: dict = {"apiKey": api_key} if api_key else {}
        f.write("[\n")
        while tries > 0:
            query_str: str = urlencode(query_dict)
            try:
                response: Response = httpx.get(url + "?" + query_str, headers=headers, follow_redirects=True,
                                               timeout=60)
                if not response or response.status_code > 399:
                    tries -= 1
                    continue

                products: list[dict] | None = parse_response(response.json() or {}, now, cutoff=cutoff,
                                                             exclude_keywords=exclude_keywords)

                if products is None:
                    logging.info("No more products left.")
                    break

                if not products:
                    logging.debug("Product is empty or all results have been filtered out.")
                else:
                    for product in products:
                        f.write(f"    {json.dumps(product)},\n")

                tries = 20
                query_dict["startIndex"] = query_dict["startIndex"] + query_dict["resultsPerPage"]

            except httpx.HTTPError as he:
                logging.warning(f"Query \"{query_str.replace('%', '%%')}\" failed.", he)
                tries -= 1
                continue
            finally:
                # Continue with the next page. Pause if necessary.
                # Because, according to the docs, one has to pause for *six* seconds at least (I'm not making this up):
                # https://nvd.nist.gov/developers/start-here
                time.sleep(pause * (20 - tries) + 1)

        f.truncate(f.tell() - 2)
        f.seek(0, 2)
        f.write("]")

        if tries <= 0:
            raise FetchError("Too many failures while reaching to the NVD endpoint. Aborting...")

    return destination_file


def parse_response(response: dict, now: str, cutoff: str = "1970-01-01T00:00:00.000",
                   exclude_keywords: list[str] = []) -> list[dict] | None:
    """

    :param response:
    :param now:
    :param cutoff:
    :param exclude_keywords:
    :return:
    """
    if response.get("resultsPerPage", 0) <= 0:
        # We have reached the end!
        return None

    products: list = list(filter(lambda y: y is not None, map(lambda x: x.get("cpe", None),
                                                              (response or {}).get("products", []))))

    # Retrieve CPE match strings.
    # Filter deprecated products, and those released *before* the cutoff timestamp, if necessary.
    # Return just the cpe name and title.
    filtered_products: list[dict] = [
        {"cpe_name": product.get("cpeName"), "title": product.get("titles", [{"title": ""}])[0].get("title")} for
        product in products if
        not (product.get("deprecated", True) and
             product.get("lastModified", now) <= cutoff) and
        any(filter(lambda x: x not in product.get("cpeName"), exclude_keywords))]

    return filtered_products
