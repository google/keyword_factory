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

echo "Setting Project ID: ${GOOGLE_CLOUD_PROJECT}"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

echo "Creating Classifier cloud function..."
gcloud functions deploy classifier-keyword-factory \
--gen2 \
--region=${GOOGLE_CLOUD_REGION} \
--runtime=python39 \
--source=./classifier/ \
--entry-point=classify \
--trigger-http \
--timeout=900s

echo "Enabling Cloud Storage service..."
gcloud services enable storage-component.googleapis.com 

echo "Enabling APIs..."
gcloud services enable googleads.googleapis.com language.googleapis.com sheets.googleapis.com

echo "Creating cloud storage bucket..."
gcloud alpha storage buckets create gs://${GOOGLE_CLOUD_PROJECT}-keyword_factory --project=${GOOGLE_CLOUD_PROJECT}

echo "Uploading config.yaml to cloud storage..."
gcloud alpha storage cp ./config.yaml gs://${GOOGLE_CLOUD_PROJECT}-keyword_factory
