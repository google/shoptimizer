# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash -u

# Import the environment variables to be used in this installer
source ./env.sh

# Constants
REGION=us-central1

if echo "$OSTYPE" | grep -q darwin
then
  PUBSUB_TOKEN=$(uuidgen)
  GREEN='\x1B[1;32m'
  NOCOLOR='\x1B[0m'
  HYPERLINK='\x1B]8;;'
else
  PUBSUB_TOKEN=$(cat /proc/sys/kernel/random/uuid)
  GREEN='\033[1;32m'
  NOCOLOR='\033[0m'
  HYPERLINK='\033]8;;'
fi

print_green() {
  echo -e "${GREEN}$1${NOCOLOR}"
}

# Authorize with a Google Account.
gcloud auth login

print_green "Shoptimizer API Installation Started."

# Set default project.
gcloud config set project "$GCP_PROJECT"

# Enable all necessary APIs.
print_green "Enabling Cloud APIs if necessary..."
REQUIRED_SERVICES=(
  cloudbuild.googleapis.com
  logging.googleapis.com
  run.googleapis.com
  sourcerepo.googleapis.com
)

ENABLED_SERVICES=$(gcloud services list)
for SERVICE in "${REQUIRED_SERVICES[@]}"
do
  if echo "$ENABLED_SERVICES" | grep -q "$SERVICE"
  then
    echo "$SERVICE is already enabled."
  else
    gcloud services enable "$SERVICE" \
      && echo "$SERVICE has been successfully enabled."
  fi
done

# Create a new Cloud Source Repository for Git
print_green "Creating the Git repository..."
EXISTING_REPOS="$(gcloud source repos list --filter="$SOURCE_REPO")"
if echo "$EXISTING_REPOS" | grep -q -w "$SOURCE_REPO"
then
  echo "Cloud Source Repository $SOURCE_REPO already exists."
else
  gcloud source repos create "$SOURCE_REPO"
fi


# Setup Service Accounts and grant permissions
print_green "Setting up service account permissions..."
PROJECT_NUMBER=$(gcloud projects list --filter="PROJECT_ID=$GCP_PROJECT" --format="value(PROJECT_NUMBER)")
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member serviceAccount:"$PROJECT_NUMBER"@cloudbuild.gserviceaccount.com \
  --role roles/iam.serviceAccountUser
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member serviceAccount:"$PROJECT_NUMBER"@cloudbuild.gserviceaccount.com \
  --role roles/container.admin
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member serviceAccount:"$PROJECT_NUMBER"@cloudbuild.gserviceaccount.com \
  --role roles/editor
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member serviceAccount:"$PROJECT_NUMBER"@cloudbuild.gserviceaccount.com \
  --role roles/run.admin

# Setup CI/CD
print_green "Deleting and re-creating Cloud Build triggers..."
CreateTrigger() {
  TARGET_TRIGGER=$1
  DESCRIPTION=$2
  ENV_VARIABLES=$3
  gcloud alpha builds triggers create cloud-source-repositories \
  --build-config=cicd/"$TARGET_TRIGGER" \
  --repo="$SOURCE_REPO" \
  --branch-pattern=main \
  --description="$DESCRIPTION" \
  --substitutions ^::^"$ENV_VARIABLES"
}

# Recreate the Cloud Build trigger.
EXISTING_TRIGGERS=$(gcloud alpha builds triggers list --filter=name:Shoptimizer | grep "id:" | awk '{printf("%s\n", $2)}')
for TRIGGER in $(echo "$EXISTING_TRIGGERS")
do
  gcloud alpha builds triggers -q delete "$TRIGGER"
done

CreateTrigger deploy_shoptimizer_to_cloud_run.yaml \
  "Shoptimizer Deploy Shoptimizer API" \
  _GCP_PROJECT="$GCP_PROJECT"

print_green "Installation and setup finished. Please deploy via Cloud Build by pushing the code to your source repository at ${HYPERLINK}https://source.cloud.google.com/$GCP_PROJECT/$SOURCE_REPO\ahttps://source.cloud.google.com/$GCP_PROJECT/$SOURCE_REPO${HYPERLINK}\a"
