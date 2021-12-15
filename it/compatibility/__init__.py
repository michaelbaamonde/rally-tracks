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

from pathlib import PurePath
from string import Template

CONFIG_DIR = os.path.join(os.getenv("RALLY_HOME", os.path.expanduser("~")), ".rally")
CONFIG_LOCATION = os.path.join(CONFIG_DIR, "rally-tracks-compatibility.ini")

def install_rally_config():
    source = os.path.join(os.path.dirname(__file__), "resources", "rally-tracks-compatibility.ini")
    repo_path = PurePath(__file__).parents[2]
    with open(CONFIG_LOCATION, "wt", encoding="utf-8") as target:
        with open(source, "rt", encoding="utf-8") as src:
            contents = src.read()
            target.write(Template(contents).substitute(LOCAL_TRACK_REPO_ROOT=repo_path, CONFIG_DIR=CONFIG_DIR))


def delete_rally_config():
    os.remove(CONFIG_LOCATION)

def setup_module():
    install_rally_config()

def teardown_module():
    delete_rally_config()
