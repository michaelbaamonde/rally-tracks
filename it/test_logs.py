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

import logging
import os

import pytest
from esrally.utils import git
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

RALLY_CLI_OPTS = {
    "target_hosts": "localhost:9200",
    "client_options": "use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'",
}

ELASTIC_PACKAGE_ENV_VARS = {
    "ELASTIC_PACKAGE_ELASTICSEARCH_HOST": "https://127.0.0.1:9200",
    "ELASTIC_PACKAGE_ELASTICSEARCH_USERNAME": "elastic",
    "ELASTIC_PACKAGE_ELASTICSEARCH_PASSWORD": "changeme",
    "ELASTIC_PACKAGE_KIBANA_HOST": "https://127.0.0.1:5601",
    "ELASTIC_PACKAGE_CA_CERT": f"{os.path.expanduser('~')}/.elastic-package/profiles/default/certs/ca-cert.pem",
}

PACKAGES = ["apache", "kafka", "mysql", "nginx", "postgresql", "redis", "system"]

RALLY_HOME = os.getenv("RALLY_HOME", os.path.expanduser("~"))
RALLY_CONFIG_DIR = os.path.join(RALLY_HOME, ".rally")
RALLY_PACKAGES_DIR = os.path.join(RALLY_CONFIG_DIR, "benchmarks", "package-storage")


@pytest.fixture(scope="module", autouse=True)
def clone_package_storage_repo():
    logger = logging.getLogger(__name__)
    if os.path.isdir(RALLY_PACKAGES_DIR):
        logger.info(f"Directory [{RALLY_PACKAGES_DIR}] already exists. Skipping clone.")
        logger.info(f"Checking out branch [production] in [{RALLY_PACKAGES_DIR}]")
        git.checkout(RALLY_PACKAGES_DIR, branch="production")
    else:
        logger.info(f"Cloning into [{RALLY_PACKAGES_DIR}]")
        git.clone(src=RALLY_PACKAGES_DIR, remote="https://github.com/elastic/package-storage")
        git.checkout(RALLY_PACKAGES_DIR, branch="production")


@pytest.fixture(scope="module")
def start_stack():
    logger = logging.getLogger(__name__)
    logger.info("Starting stack services")
    run_command_with_output("elastic-package stack up -d -v")
    logger.info("Stack services started")
    yield
    logger.info("Stopping stack services")
    run_command_with_output("elastic-package stack down -v")
    logger.info("Stack services stopped")


@pytest.fixture(scope="module", autouse=True)
def install_packages(start_stack):
    logger = logging.getLogger(__name__)
    for package in PACKAGES:
        package_root = f"{RALLY_PACKAGES_DIR}/packages/{package}"
        latest_version = sorted(os.listdir(package_root))[-1]
        cmd = f"elastic-package install -R {package_root}/{latest_version} -v"
        logger.info("Running command: [%s]", cmd)
        run_command_with_output(cmd, env={**os.environ, **ELASTIC_PACKAGE_ENV_VARS})
    yield


def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}


class TestLogs:
    def test_logs_default(self, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(),
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_disk_usage(self, rally):
        custom = {"number_of_shards": 4}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-disk-usage",
            track_params=params(updates=custom),
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_indexing_unthrottled(self, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(),
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_querying(self, rally):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_indexing_querying_unthrottled(self, rally):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_indexing_throttled(self, rally):
        custom = {"throttle_indexing": "true"}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(updates=custom),
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_indexing_querying_throttled(self, rally):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
            "throttle_indexing": "true",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            **RALLY_CLI_OPTS,
        )
        assert ret == 0

    def test_logs_querying_with_preloaded_data(self, rally):
        custom = {
            "bulk_start_date": "2020-09-30T00-00-00Z",
            "bulk_end_date": "2020-09-30T00-00-02Z",
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom),
            **RALLY_CLI_OPTS,
        )
        assert ret == 0
