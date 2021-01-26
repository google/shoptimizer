# Shoptimizer API Install Guide

_Copyright 2019 Google LLC. This solution, including any related sample code or
data, is made available on an “as is,” “as available,” and “with all faults”
basis, solely for illustrative purposes, and without warranty or representation
of any kind. This solution is experimental, unsupported and provided solely for
your convenience. Your use of it is subject to your agreements with Google, as
applicable, and may constitute a beta feature as defined under those agreements.
To the extent that you make any data available to Google in connection with your
use of the solution, you represent and warrant that you have all necessary and
appropriate rights, consents and permissions to permit Google to use and process
that data. By using any portion of this solution, you acknowledge, assume and
accept all risks, known and unknown, associated with its usage, including with
respect to your deployment of any portion of this solution in your systems, or
usage in connection with your business, if at all._

[TOC]

## 0. About

This document explains how to build and run the Shoptimizer API (referred to as 'Shoptimizer').

For an explanation of how to integrate Shoptimizer with your existing codebase and for more technical details, see the [developer guide](./developer-guide.md).

## 1. Prerequisites

* An environment capable of hosting Docker containers (for example, [Google Cloud Run](https://cloud.google.com/run))


## 2. Installing Shoptimizer

This section describes how to download, build, and run Shoptimizer.

Note: For details on how to run a container image on your chosen platform besides GCP, which is described below, see the documentation for your specific platform.

### 2.1 Installing to GCP Cloud Run automatically

If you do not have a container host already, you can use [Google Cloud Run](https://cloud.google.com/run) to host Shoptimizer.

Prerequisites: Using the automated install script requires a Google Cloud project with a billing account attached, as well have having installed the [Google Cloud SDK Command-Line Tools](https://cloud.google.com/sdk).

#### 2.1.1 Clone the Solution and set environment variables

Git clone the repository:

`git clone https://github.com/google/shoptimizer.git`

Navigate to the Shoptimizer directory:

`cd shoptimizer/shoptimizer_api`

Edit the env.sh file:

`vim env.sh`

Set the following variables to names you choose:

`GCP_PROJECT=[YOUR_GCP_PROJECT_NAME]`

`SOURCE_REPO=[NAME_FOR_YOUR_GIT_REPO_IN_GCP]`

#### 2.1.2 Run the command-line installation script

Set the GCP project to your target project in your command prompt:

`gcloud config set project [YOUR_GCP_PROJECT_NAME]`

Run the installation script:

`sh install_to_gcp.sh`

#### 2.1.3 Start the deployment using the installed GCP Cloud Build trigger

Set the remote destination for your Cloud project's git repo. You can copy the destination URL from the Source Repo page accessed from your GCP project's admin console, or replace the variables in the command shown below:

`git remote add gcp ssh://[YOUR_USERNAME]@source.developers.google.com:2022/p/[YOUR_GCP_PROJECT_NAME]/r/[NAME_FOR_YOUR_GIT_REPO_IN_GCP]`

Finally, push the code to your GCP project's Cloud Source Repository.

`git push gcp master`

Allow the deployment to run in Cloud Build. This will take several minutes. You can monitor the progress from your GCP project's Cloud Build dashboard in the admin console.

Congratulations, you should now have Shoptimizer running in Docker on Cloud Run!

### 2.2 Installing to GCP Cloud Run manually

This section explains how to set up Shoptimizer on Google Cloud Run using CLI.

#### 2.2.1 Install Docker and set up the Cloud SDK.

You should have [Docker](https://docs.docker.com/get-docker/) installed.

Install the [Google Cloud SDK](https://cloud.google.com/sdk/install).

After it is installed, configure Docker for gcloud:

`gcloud auth configure-docker`

#### 2.2.2 Build the Image

If you are not already in the Shoptimizer directory, navigate to that directory with the following command:

`cd shoptimizer/shoptimizer_api`

Then, build the image:

`docker build . -t gcr.io/[project-id]/shoptimizer`

(Replace [project-id] with your Google Cloud Platform project ID.)

#### 2.2.3 Push the Image to the GCR

Push the image you just built to Google Container Registry:

`docker push gcr.io/[project-id]/shoptimizer`

(Replace [project-id] with your Google Cloud Platform project ID.)

#### 2.2.4 Deploy to Cloud Run

Deploy the container to Cloud Run:

`gcloud run deploy --image gcr.io/[project-id]/shoptimizer --platform managed`

(Replace [project-id] with your Google Cloud Platform project ID.)

When prompted, select the following options:

    Set servicename: shoptimizer
    Allow unauthenticated invocations: N

Take note of the URL returned. It should look something like this:

`https://shoptimizer-abcde12345-an.a.run.app`

Congratulations, you should now have Shoptimizer running in Docker on Cloud Run!

### 2.3 Build and run Shoptimizer on Docker (local)

#### 2.3.1 Clone the Solution

Git clone the repository:

`git clone https://github.com/google/shoptimizer.git`

#### 2.3.2 Build the Image

Navigate to the Shoptimizer directory:

`cd shoptimizer/shoptimizer_api`

Run the following command to build the image:

`docker build -t shoptimizer .`

_Optional: To check that the image built correctly, run `docker image ls` and confirm that 'shoptimizer' is in the list of images._

#### 2.3.3 Run the Container

After building the image, run the container with the following command:

`docker run -d --name shoptimizer -p 8080:8080 -e PORT=8080 -e PRODUCT_TRACKING_FIELD="customLabel4" shoptimizer`

_Optional: To check that the container started correctly, run `docker container ps -a` and check the 'shoptimizer' STATUS._

#### Note on Environment Variables:

The shoptimizer container contains the following environment variables:

* __PORT__:
The port for the gunicorn server that is used to run Shoptimizer.

* __PRODUCT_TRACKING_FIELD__:
A field used to track the performance of optimized products in Google Ads. Specifically, when products are modified by Shoptimizer, this field will be set to one of three options:

     - __SANITIZED__:
Invalid data was removed or corrected. If this had not been done the product would have been disapproved.
     - __OPTIMIZED__:
 Data was modified in an attempt to improve performance, but the original data was not incorrect.
     - __SANITIZED_AND_OPTIMIZED__:
The product was both sanitized and optimized.

    These three values can be used as filters in Google Ads to track the performance of products affected by Shoptimizer. Setting this variable to an empty string will disable tracking. The default value is 'customLabel4'.

## 3. Testing the Shoptimizer API

### 3.1 Local testing

You can check if your container is working correctly by sending a request to the following URL:

`{HOST}:{PORT}/shoptimizer/v1/health`

For example, if you are running the container on localhost with a port of 8080, you can test it by going to the following URL:

`http://localhost:8080/shoptimizer/v1/health`

### 3.2 Testing on GCP Cloud Run

Make a request to the API to check it is working by running the following command:

    curl -H \
    "Authorization: Bearer $(gcloud auth print-identity-token)" \
    [YOUR_SHOPTIMIZER_URL]/shoptimizer/v1/health

Example:

    curl -H \
    "Authorization: Bearer $(gcloud auth print-identity-token)" \
    https://shoptimizer-adcde12345-an.a.run.app/shoptimizer/v1/health


It should return, ``Success``.

If you do not see `Success`, check the Google Cloud Platform > Cloud Run UI and make sure your container is up and running correctly.

## 4. Container Security
The Shoptimizer API by default does not provide authentication or authorization mechanisms. If you want to secure the container, use the security mechanisms provided by your container host.

For example, if using Google Cloud Run, restrict the container to only allow authenticated invocations and use 'Permissions' to grant access to your application's service account.

## 5. Updating Shoptimizer
To update Shoptimizer, check the Releases section to download new versions of the API as they are released, and perform a re-deployment of the container.
