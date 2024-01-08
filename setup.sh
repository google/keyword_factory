#!/bin/bash
# ansi colors
COLOR='\033[0;36m' # Cyan
NC='\033[0m'
RED='\033[0;31m'

SETTING_FILE="./settings.ini"
SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
SETTING_FILE="${SCRIPT_PATH}/settings.ini"

# changing the cwd to the script's contining folder so all pathes inside can be local to it
# (important as the script can be called via absolute path and as a nested path)
pushd $SCRIPT_PATH >/dev/null

while :; do
    case $1 in
  -s|--settings)
      shift
      SETTING_FILE=$1
      ;;
  *)
      break
    esac
  shift
done

PROJECT_ID=$(gcloud config get-value project 2> /dev/null)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="csv(projectNumber)" | tail -n 1)
SERVICE_ACCOUNT=$PROJECT_NUMBER-compute@developer.gserviceaccount.com

GCS_BUCKET=gs://${PROJECT_ID}
GCS_PATH=$GCS_BUCKET/keyword_factory
CONFIG_PATH=$GCS_PATH/config.yaml
CLASSIFIER_FUNCTION_NAME=classifier-keyword-factory

REGION=$GOOGLE_CLOUD_REGION
if [ ! $REGION ]; then
  REGION=$(git config -f $SETTING_FILE gcp.region)
fi

check_billing() {
  BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="csv(billingEnabled)" | tail -n 1)
  if [[ "$BILLING_ENABLED" = 'False' ]]
  then
    echo -e "${RED}The project $PROJECT_ID does not have a billing enabled. Please activate billing${NC}"
    exit -1
  fi
}

enable_apis() {
  echo "${COLOR}Enabling container deployment...${NC}"
  gcloud auth configure-docker
  echo -e "${COLOR}Enabling APIs...${NC}"
  gcloud services enable storage-component.googleapis.com
  gcloud services enable googleads.googleapis.com \
    language.googleapis.com \
    sheets.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    cloudfunctions.googleapis.com \
    run.googleapis.com
}

create_gcs_bucket() {
  echo -e "${COLOR}Creating cloud storage bucket...${NC}"
  if ! gsutil ls $GCS_BUCKET > /dev/null 2> /dev/null; then
    gsutil mb -b on $GCS_BUCKET
    echo "Bucket $GCS_BUCKET created"
  else
    echo "Bucket $GCS_BUCKET already exists"
  fi
}

deploy_files() {
  if [[ -f ./config.yaml ]]; then
    echo -e "${COLOR}Uploading files to GCS...${NC}"
    gsutil cp config.yaml $GCS_PATH
    echo -e "${COLOR}Files were deployed to ${GCS_PATH}${NC}"
  fi
}

deploy_cf() {
  echo -e "${COLOR}Creating Classifier Cloud function...${NC}"
  gcloud functions deploy $CLASSIFIER_FUNCTION_NAME \
    --gen2 \
    --region=$REGION \
    --runtime=python310 \
    --source=./classifier/ \
    --entry-point=classify \
    --trigger-http \
    --timeout=3600s \
    --set-env-vars "config_path"="$CONFIG_PATH"
}

deploy_app() {
  echo -e "${COLOR}Building and deploying Cloud Run application...${NC}"

  IMAGE="keyword-factory"
  gcloud builds submit --config=cloudbuild-gcr.yaml --substitutions=_IMAGE=$IMAGE .

  MEMORY=$(git config -f $SETTING_FILE cloud-run.memory)
  CPU=$(git config -f $SETTING_FILE cloud-run.cpu)
  gcloud run deploy keyword-factory \
    --platform=managed \
    --image=gcr.io/$PROJECT_ID/$IMAGE \
    --region=$REGION \
    --allow-unauthenticated \
    --set-env-vars "config_path"="$CONFIG_PATH","cf_classifier_name"="$CLASSIFIER_FUNCTION_NAME" \
    --execution-environment=gen2 \
    --timeout=3600 \
    --max-instances=1 \
    --memory=$MEMORY \
    --cpu=$CPU
}


deploy_all() {
  check_billing
  enable_apis
  create_gcs_bucket
  deploy_files
  deploy_cf
  #deploy_app
}


_list_functions() {
  # list all functions in this file not starting with "_"
  declare -F | awk '{print $3}' | grep -v "^_"
}


if [[ $# -eq 0 ]]; then
  _list_functions
else
  for i in "$@"; do
    if declare -F "$i" > /dev/null; then
      "$i"
      exitcode=$?
      if [ $exitcode -ne 0 ]; then
        echo "Breaking script as command '$i' failed"
        exit $exitcode
      fi
    else
      echo -e "\033[0;31mFunction '$i' does not exist.\033[0m"
    fi
  done
fi

popd > /dev/null
