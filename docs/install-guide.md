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

_Note: For  instructions on how to run a container image on your chosen platform (e.g., Google Cloud Run), see documentation for that platform._

### 2.1 Clone the Solution

Git clone the repository:

`git clone -b master https://cse.googlesource.com/solutions/shopping_feed_optimizer`

If you get an error stating:
`remote: PERMISSION_DENIED: The caller does not have permission`
Please visit https://cse.googlesource.com/new-password and follow the instructions

### 2.2 Build the Image

Navigate to the Shoptimizer directory:

`cd shopping_feed_optimizer/shoptimizer_api`

Run the following command to build the image:

`docker build -t shoptimizer .`

_Optional: To check that the image built correctly, run `docker image ls` and confirm that 'shoptimizer' is in the list of images._

### 2.3 Run the Container

After building the image, run the container with the following command:

`docker run -d --name shoptimizer -p 8080:8080 -e PORT=8080 -e PRODUCT_TRACKING_FIELD="customLabel4" shoptimizer`

_Optional: To check that the container started correctly, run `docker container ps -a` and check the 'shoptimizer' STATUS._

#### Note on Environment Variables

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


### 2.4 Test the API
You can check if your container is working correctly by sending a request to the following URL:

`{HOST}:{PORT}/shoptimizer/v1/health`

For example, if you are running the container on localhost with a port of 8080, you can test it by going to the following URL:

`http://localhost:8080/shoptimizer/v1/health`

## 3. Container Security
The Shoptimizer API does not provide authentication or authorization mechanisms. If you want to secure the container, use the security mechanisms provided by your container host.

For example, if using Google Cloud Run, restrict the container to only allow authenticated invocations and use 'Permissions' to grant access to your application's service account.

## 4. Updating Shoptimizer
To update Shoptimizer, repeat step 2 whenever a code update is available.

## 5. Installing to Cloud Run (Optional)

If you do not have a container host already, you can use [Google Cloud Run](https://cloud.google.com/run) to host Shoptimizer.

This section explains how to set up Shoptimizer on Google Cloud Run using CLI.

### 5.1 Set Up the SDK

Install the [Google Cloud SDK](https://cloud.google.com/sdk/install).

After it is installed, configure Docker for gcloud:

`gcloud auth configure-docker`

### 5.2 Build the Image

If you are not already in the Shoptimizer directory, navigate to that directory with the following command:

`cd shopping_feed_optimizer/shoptimizer_api`

Then, build the image:

`docker build . -t gcr.io/[project-id]/shoptimizer`

(Replace [project-id] with your Google Cloud Platform project ID.)

### 5.3 Push the Image to the GCR

Push the image you just built to Google Container Registry:

`docker push gcr.io/[project-id]/shoptimizer`

(Replace [project-id] with your Google Cloud Platform project ID.)

### 5.4 Deploy to Cloud Run

Deploy the container to Cloud Run:

`gcloud run deploy --image gcr.io/[project-id]/shoptimizer --platform managed`

(Replace [project-id] with your Google Cloud Platform project ID.)

When prompted, select the following options:

    Set servicename: shoptimizer
    Allow unauthenticated invocations: N

Take note of the URL returned. It should look something like this:

`https://shoptimizer-abcde12345-an.a.run.app`

### 5.5 Test the API

Make a request to the API to check it is working by running the following command:

    "Authorization: Bearer $(gcloud auth print-identity-token)" \
    [URL-from-step-5.1]/shoptimizer/v1/health

Example:

    curl -H \
    "Authorization: Bearer $(gcloud auth print-identity-token)" \
    https://shoptimizer-adcde12345-an.a.run.app/shoptimizer/v1/health


It should return, ``Success``.

If you do not see `Success`, check the Google Cloud Platform > Cloud Run UI and make sure your container is up and running correctly.
