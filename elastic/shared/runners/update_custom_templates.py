# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import os
from pathlib import Path

async def update_custom_templates(es, params):
    custom = {
      "template" : {
        "settings": {
          "index" : {
              "number_of_replicas" : 1,
              "number_of_shards" : 1,
          }
        },
        "mappings" : {
            "runtime": {
                "rally.doc_size": {
                    "type": "long"
                },
                "rally.message_size": {
                    "type": "long"
                }
            },
            "properties" : {
                "event": {
                    "properties": {
                        "created": {
                            "type": "date",
                            "format": "strict_date_optional_time"
                        },
                        "ingested": {
                            "type": "date",
                            "format": "strict_date_optional_time"
                        }
                    }
                }
            }
        }
      }
    }

    resp = await es.cluster.get_component_template()
    ops_count = 0

    for template in resp["component_templates"]:
        name = template["name"]
        if name.endswith("@custom"):
            original = template["component_template"]
            new = {**original, **custom}
            await es.cluster.put_component_template(name=name, body=new)
            ops_count += 1

    return {
        "weight": ops_count,
        "unit": "ops",
        "success": True,
    }
