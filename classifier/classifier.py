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
import logging 

class Classifier():
    def __init__(self):
        self.client = language_v1.LanguageServiceClient()
        self.type_ = language_v1.Document.Type.PLAIN_TEXT
        self.content_categories_version = (
        language_v1.ClassificationModelOptions.V2Model.ContentCategoriesVersion.V2
    )
        
    def classify_list(self, kw_list, language='en'):
        results = {}
        for kw in kw_list:
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
                    results[kw] = {
                        "full category": category.name,
                        "confidence": category.confidence
                    }
                    break

            except Exception as e:
                logging.exception(e)
                results[kw] = {
                    "full category": '',
                    "confidence": None
                }
        
        return results