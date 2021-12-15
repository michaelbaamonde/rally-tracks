# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import shlex
import subprocess
import uuid

import pytest

from pathlib import PurePath
from esrally import client

class ESCluster:
    def __init__(self):
        self.installation_id = None
        self.http_port = None

    def install(self, node_name, car, http_port):
        self.http_port = http_port
        transport_port = http_port + 100
        try:
            cmd = (f"esrally install --quiet "
                   f"--http-port={http_port} --node={node_name} --master-nodes={node_name} --car={car} "
                   f'--seed-hosts="127.0.0.1:{transport_port}"')
            output = subprocess.run(shlex.split(cmd), text=True, capture_output=True, check=True)
            self.installation_id = json.loads("".join(output.stdout))["installation-id"]
        except subprocess.CalledProcessError as e:
            raise AssertionError(f"Failed to install Elasticsearch", e)

    def start(self, race_id):
        cmd = f'esrally start --runtime-jdk=bundled --installation-id={self.installation_id} --race-id={race_id}'
        try:
            subprocess.run(shlex.split(cmd), check=True)
        except subprocess.CalledProcessError as e:
            raise AssertionError("Failed to start Elasticsearch test cluster.", e)
        es = client.EsClientFactory(hosts=[{"host": "127.0.0.1", "port": self.http_port}], client_options={}).create()
        client.wait_for_rest_layer(es)

    def stop(self):
        if self.installation_id:
            try:
                cmd = f"esrally stop --installation-id={self.installation_id}"
                subprocess.run(shlex.split(cmd))
            except subprocess.CalledProcessError as e:
                raise AssertionError("Failed to stop Elasticsearch test cluster.", e)

    def __str__(self):
        return f"ESCluster[installation-id={self.installation_id}]"

@pytest.fixture(scope="module", autouse=True)
def test_cluster():
    cluster = ESCluster()
    port = 19200
    race_id = str(uuid.uuid4())

    #wait_until_port_is_free(port_number=port)
    cluster.install(node_name="rally-node", car="4gheap,basic-license", http_port=port)
    cluster.start(race_id=race_id)
    yield cluster
    cluster.stop()

@pytest.fixture(scope="module")
def track_path():
    return PurePath(__file__).parents[2]

@pytest.fixture(scope="module")
def track_revision(pytestconfig, track_path):
    provided_revision = pytestconfig.getoption("revision")
    if provided_revision is not None:
        return provided_revision
    else:
        proc = subprocess.run(shlex.split(f"git -C {track_path} rev-parse HEAD"), text=True, capture_output=True)
        return proc.stdout


def list_tracks():
    cmd = "esrally list tracks --config=rally-tracks-compatibility.ini"
    proc = subprocess.run(shlex.split(cmd), text=True, capture_output=True)
    return proc.stdout


def all_tracks_and_challenges():
    ret = []

    # The first 13 lines are the Rally banner and table formatting
    # The last 4 are blank or informational
    track_list = list_tracks().split("\n")[12:-5]
    for track_str in track_list:
        track_name, *_, challenge_str = track_str.split()
        challenges = challenge_str.split(",")
        ret.append((track_name, challenges))
    return ret


def track_challenge_pairs(tracks, all_tracks):
    ret = []

    for track, challenges in all_tracks:
        if track in tracks:
            for challenge in challenges:
                ret.append((track, challenge))

    return ret


def pytest_addoption(parser):
    parser.addoption("--track", action="append", default=[], help="Track to test")
    parser.addoption("--revision", action="store", default=None, help="Track revision to test")


def pytest_generate_tests(metafunc):
    if "track" and "challenge" in metafunc.fixturenames:
        all_tracks = all_tracks_and_challenges()
        tracks = metafunc.config.getoption('track') or [track for (track, _) in all_tracks]

        metafunc.parametrize("track,challenge", track_challenge_pairs(tracks, all_tracks))
