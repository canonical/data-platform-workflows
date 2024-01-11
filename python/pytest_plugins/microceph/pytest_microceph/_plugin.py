import dataclasses
import json
import logging
import subprocess

import boto3
import pytest


@dataclasses.dataclass(frozen=True)
class ConnectionInformation:
    access_key_id: str
    secret_access_key: str
    bucket: str


@pytest.fixture(scope="session")
def microceph():
    # todo: check if running in CI?
    logger.info("Setting up microceph")
    subprocess.run(["sudo", "snap", "install", "microceph"], check=True)
    subprocess.run(["sudo", "microceph", "cluster", "bootstrap"], check=True)
    subprocess.run(["sudo", "microceph", "disk", "add", "loop,4G,3"], check=True)
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
    return ConnectionInformation(key_id, secret_key, _BUCKET)


_BUCKET = "testbucket"
logger = logging.getLogger(__name__)
