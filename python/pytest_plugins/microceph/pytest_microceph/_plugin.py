import dataclasses
import json
import logging
import os
import subprocess

import boto3
import pytest


MICROCEPH_URL = "http://localhost"
MICROCEPH_REGION = "default"


@dataclasses.dataclass(frozen=True)
class ConnectionInformation:
    endpoint: str
    region: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    keep_after_finished: bool


@pytest.fixture(scope="session")
def microceph(request):
    if not os.environ.get("CI") == "true":
        raise Exception("Not running on CI. Skipping microceph installation")
    if "microceph" in subprocess.check_output(
        ["sudo", "snap", "list"]
    ).decode():
        logger.info("Microceph already set, leaving...")
        return
    logger.info("Setting up microceph")
    subprocess.run(["sudo", "snap", "install", "microceph"], check=True)
    subprocess.run(["sudo", "microceph", "cluster", "bootstrap"], check=True)
    subprocess.run(
        ["sudo", "microceph", "disk", "add", "loop,4G,3"],
        check=True
    )
    subprocess.run(["sudo", "microceph", "enable", "rgw"], check=True)
    output = subprocess.run(
        [
            "sudo",
            "microceph.radosgw-admin",
            "user",
            "create",
            "--uid",
            "test",
            "--display-name",
            "test",
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout
    key = json.loads(output)["keys"][0]
    key_id = key["access_key"]
    secret_key = key["secret_key"]
    logger.info("Creating microceph bucket")
    boto3.client(
        "s3",
        endpoint_url="http://localhost",
        aws_access_key_id=key_id,
        aws_secret_access_key=secret_key,
    ).create_bucket(Bucket=_BUCKET)
    logger.info("Set up microceph")
    return ConnectionInformation(
        MICROCEPH_URL,
        MICROCEPH_REGION,
        key_id,
        secret_key,
        _BUCKET,
        request.config.option.keep_microceph
    )


_BUCKET = "testbucket"
logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--keep-microceph",
        action="store_true",
        help="Does not delete microceph at the end of the test.",
    )


@pytest.fixture(scope="session", autouse=True)
def clean_microceph(microceph):
    yield

    if "microceph" not in subprocess.check_output(
        ["sudo", "snap", "list"]
    ).decode():
        logger.info("Microceph not installed, leaving...")
        return
    if microceph.keep_after_finished:
        logger.debug("Keeping microceph running as requested")
        return
    subprocess.run(
        ["sudo", "snap", "remove", "--purge", "microceph"],
        check=True
    )
