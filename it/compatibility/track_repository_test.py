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

import pytest

class TestTrackRepository:
#     track_challenges_to_skip = {
#         "sql": ["sql"],
# #        "http_logs": ["append-no-conflicts", "runtime-fields"]
#     }

    overrides = {
        "http_logs": {
            "runtime-fields": {
                "enable_assertions": False
            },
            "append-no-conflicts": {
                "enable_assertions": False
            }

        },
        "sql": {
            "sql": {
                "track_params": "ingest_percentage:1,query_percentage:2"
            }
        }
    }
    def test_track_challenge(self, rally_config, es_cluster, race, track, challenge):
        kwarg_overrides = self.overrides.get(track, {}).get(challenge, {})
        ret = race(track, challenge, **kwarg_overrides)
        assert ret == 0

# class TestHttpLogs:
#     def test_http_logs_runtime_fields(self, rally_config, es_cluster, race):
#         ret = race("http_logs", "runtime-fields", enable_assertions=False)

#     def test_http_logs_append_no_conflicts(self, rally_config, es_cluster, race):
#         ret = race("http_logs", "append_no_conflicts", enable_assertions=False)
