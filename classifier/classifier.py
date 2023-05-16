# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import language_v1
from google.api_core.exceptions import ResourceExhausted
from time import sleep
import logging 

_MAX_KW_CAT = 30000

class Classifier():
    def __init__(self):
        self.client = language_v1.LanguageServiceClient()
        self.type_ = language_v1.Document.Type.PLAIN_TEXT
        self.content_categories_version = (
        language_v1.ClassificationModelOptions.V2Model.ContentCategoriesVersion.V2
    )
        
    def classify_list(self, kw_list, language='en'):
        results = {}
        counter = 0
        while counter < min(_MAX_KW_CAT, len(kw_list)):
            kw = kw_list[counter]
            document = {
                "content": kw,
                "type_": self.type_,
                "language": language
            }
            try:
                response = self.client.classify_text(
                    request={
                        "document": document,
                        "classification_model_options": {
                            "v2_model": {"content_categories_version": self.content_categories_version}
                        }
                    }
                )
                if not response.categories:
                    results[kw] = {
                        "full category": '',
                        "confidence": None
                    } 
                for category in response.categories:
                    results[kw + str(counter)] = {
                        "full category": category.name,
                        "confidence": category.confidence
                    }
                    break
                counter += 1

            except ResourceExhausted as re:
                sleep(2)

            except Exception as e:
                logging.exception(e)
                results[kw + str(counter)] = {
                    "full category": '',
                    "confidence": None
                }
                counter += 1

        return results