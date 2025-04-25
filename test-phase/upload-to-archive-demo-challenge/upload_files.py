"""
This script shows an example how to use GC-API to programmatically upload
files to an archive.

Remember, an archive is used to pull data per phase for a challenge. Each
phase has a designated archive. The archive is approached using its slug.

For your challenge, and this phase it is 'demo-challenge'.

Before you can run this script, you need to:
 * install gc-api (`pip install gcapi`)
 * update the EXPECTED_FILES
 * update the API_TOKEN with a personal token

Get a token from Grand Challenge:
  https://grand-challenge.org/settings/api-tokens/create/

For additional information about using gc-api and tokens, visit:
  https://grand-challenge.org/documentation/what-can-gc-api-be-used-for/#your-personal-api-token

Note that Grand-Challenge does its own post-processing on the files and the archive
will be filled with the result of this post-processing.

Check your uploaded results here:
 https://grand-challenge.org/archives/demo-challenge/

And the intermediate processing state here:
  https://grand-challenge.org/cases/uploads/

Happy uploading!
"""

from pathlib import Path

import gcapi
import json

API_TOKEN = "REPLACE-ME-WITH-YOUR-TOKEN"

ARCHIVE_SLUG = "demo-challenge"


EXPECTED_CASE_FILES_FOR_INTERFACE_0 = [
    {
        "color-fundus-image": "test-phase/upload-to-archive-demo-challenge/interface_0/case_0/images/color-fundus",
        "age-in-months": "test-phase/upload-to-archive-demo-challenge/interface_0/case_0/age-in-months.json",
    },
    {
        "color-fundus-image": "test-phase/upload-to-archive-demo-challenge/interface_0/case_1/images/color-fundus",
        "age-in-months": "test-phase/upload-to-archive-demo-challenge/interface_0/case_1/age-in-months.json",
    },
    {
        "color-fundus-image": "test-phase/upload-to-archive-demo-challenge/interface_0/case_2/images/color-fundus",
        "age-in-months": "test-phase/upload-to-archive-demo-challenge/interface_0/case_2/age-in-months.json",
    },
]


EXPECTED_CASES = [
    *EXPECTED_CASE_FILES_FOR_INTERFACE_0,
]

EXPECTED_SOCKETS = [
    {
        "color-fundus-image",
        "age-in-months",
    },
]


def main():
    pre_flight_check()
    upload_files()
    return 0


def pre_flight_check():
    # Perform a sanity-check to see if everything is in place
    # before we start uploading files to the archive

    for case in EXPECTED_CASES:
        prepare_contents(case)


def upload_files():
    # Uploads files to the Grand-Challenge archive

    client = gcapi.Client(token=API_TOKEN)
    archive = client.archives.detail(slug=ARCHIVE_SLUG)
    archive_api_url = archive["api_url"]

    for case in EXPECTED_CASES:
        print(f"Uploading {case} to {archive['title']}")

        contents = prepare_contents(case)
        archive_item = client.archive_items.create(archive=archive_api_url, values=[])
        client.update_archive_item(
            archive_item_pk=archive_item["pk"],
            values=contents,
        )


def prepare_contents(case):
    contents = {}

    socket_set = set(case.keys())
    assert (
        socket_set in EXPECTED_SOCKETS
    ), f"The input socket set {socket_set} is unexpected and probably incorrect!"

    for slug, file in case.items():
        file_path = Path(file)
        assert file_path.exists(), f"File {file} does not exist"

        if slug == "color-fundus-image":
            contents[slug] = list(file_path.rglob("*"))
            assert contents[slug], f"No files found in {slug}"
        elif slug == "age-in-months":
            contents[slug] = json.loads(file_path.read_text())
        else:
            raise RuntimeError(f"Unexpected socket: {key}")

    return contents


if __name__ == "__main__":
    raise SystemExit(main())
