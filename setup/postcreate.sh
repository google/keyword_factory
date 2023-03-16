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

cf_uri=$(gcloud functions describe classifier-keyword-factory --format 'value(serviceConfig.uri)')
project_number=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
service_account="serviceAccount:${project_number}-compute@developer.gserviceaccount.com"

echo "Setting environment variable.." 
gcloud run services update keyword-factory --update-env-vars bucket_name=${GOOGLE_CLOUD_PROJECT}-keyword_factory,cf_uri=$cf_uri --region=${GOOGLE_CLOUD_REGION}

echo "Setting service account permissions"
gcloud run services add-iam-policy-binding 'classifier-keyword-factory' \
  --member=$service_account \
  --role='roles/run.invoker' \
  --region=${GOOGLE_CLOUD_REGION}