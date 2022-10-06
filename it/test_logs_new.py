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

import os

import pytest

from pytest_rally.process import run_command_with_output

BASE_PARAMS = {
    "start_date": "2021-01-01T00-00-00Z",
    "end_date": "2021-01-01T00-00-02Z",
    "max_total_download_gb": "18",
    "raw_data_volume_per_day": "72GB",
    "max_generated_corpus_size": "1GB",
    "wait_for_status": "green",
    "force_data_generation": "true",
    "number_of_shards": "2",
    "number_of_replicas": "0",
}

ELASTIC_PACKAGE_ENV_VARS = {
    "ELASTIC_PACKAGE_ELASTICSEARCH_HOST": "https://127.0.0.1:9200",
    "ELASTIC_PACKAGE_ELASTICSEARCH_USERNAME": "elastic",
    "ELASTIC_PACKAGE_ELASTICSEARCH_PASSWORD": "changeme",
    "ELASTIC_PACKAGE_KIBANA_HOST": "https://127.0.0.1:5601",
    "ELASTIC_PACKAGE_CA_CERT": "$HOME/.elastic-package/profiles/default/certs/ca-cert.pem"
}

PACKAGES = [
    "apache/1.3.5",
    "kafka/1.2.2",
    "mysql/1.2.1",
    "nginx/1.4.1",
    "postgresql/1.4.1",
    "redis/1.2.0",
    "system/1.19.3"
]


@pytest.fixture(scope="module")
def start_stack():
    run_command_with_output("elastic-package stack up -d -v")
    yield
    run_command_with_output("elastic-package stack down -v")

@pytest.fixture(scope="module")
def install_packages(start_stack):
    for package in PACKAGES:
        root = f"/home/baamonde/code/elastic/package-storage/packages/{package}"
        cmd = f"elastic-package install -R {root} -v"
        run_command_with_output(cmd, env={**os.environ, **ELASTIC_PACKAGE_ENV_VARS})
    yield

def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}


class TestLogs:
    def test_logs_default(self, rally, install_packages):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params="number_of_replicas:0",
            target_hosts="localhost:9200",
            client_options="use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'",
        )
        assert ret == 0
