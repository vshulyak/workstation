# Workstation

Run your Data Science environment anywhere on localhost or on EC2.

# Motivation

I mainly work on my laptop but occasionally there's a need to compute something on a GPU or on a machine with lots of memory.
With this setup I can spin up any EC2 machine and pickup my work where I left off quickly on the new remote env.

# Features

* Run the same environment on your laptop and on any EC2 instance (with/without GPU).
* All notebooks are stored on versioned S3 buckets, accessible from any environment.
* Run the environment on preemptible EC2 instances, without the fear to lose your progress.
* Has Tensorboard & MLFlow already configured and running by default.

# Known Issues

* Long time to build, push, and pull the image.
* Hard to update dependencies.

# Components

* This repo for managing containers.
* [![CircleCI](https://circleci.com/gh/vshulyak/workstation_image/tree/master.svg?style=svg)](https://circleci.com/gh/vshulyak/workstation_image/tree/master)
[![](https://images.microbadger.com/badges/image/vshulyak/workstation_image.svg)](https://microbadger.com/images/vshulyak/workstation_image "Get your own image badge on microbadger.com") with the actual environment.
* [![CircleCI](https://circleci.com/gh/vshulyak/workstation_base/tree/master.svg?style=svg)](https://circleci.com/gh/vshulyak/workstation_base/tree/master)
[![](https://images.microbadger.com/badges/image/vshulyak/workstation_base.svg)](https://microbadger.com/images/vshulyak/workstation_base "Get your own image badge on microbadger.com") with basic dependencies – Python, Miniconda, CUDNN, Java.


# Installation

TBD

## Example .env file

```
JUPYTER_PASS_HASH=sha1:<salt>:<hash>
JUPYTER_NB_BUCKET=<notebooks_s3_bucket_name>
JUPYTER_NB_BUCKET_PREFIX=notebooks
JUPYTER_NB_BUCKET_REGION=<aws_region>
JUPYTER_NB_BUCKET_MOUNT=/mnt/notebooks
JUPYTER_DATA_BUCKET=<datasets_s3_bucket_name>
JUPYTER_DATA_BUCKET_PREFIX=datasets
JUPYTER_DATA_BUCKET_REGION=<aws_region>
JUPYTER_DATA_BUCKET_MOUNT=/mnt/data
AWS_ACCESS_KEY=<>
AWS_SECRET_KEY=<>

MLFLOW_DATA_BUCKET=<mlflow_s3_bucket_name>
MLFLOW_DATA_BUCKET_PREFIX=
MLFLOW_DATA_BUCKET_REGION=<aws_region>
MLFLOW_DATA_BUCKET_MOUNT=/mnt/mlflow
MLFLOW_SERVER_PERSISTENT_DISK_PATH=/mnt/mlflow/persistent_disk
MLFLOW_SERVER_ARTIFACTS=/mnt/mlflow/artifacts
MLFLOW_SERVER_HOST=0.0.0.0
MLFLOW_SERVER_PORT=5000
MLFLOW_TRACKING_URI=http://localhost:5000

TENSORBOARD_LOGS_DIR=/tmp/tflogs/
```

# TODO

* Migrate to the new version of docker-compose
* Migrate to fabric2
* Cleanup AWS management scripts
* Auto-install tensorflow-gpu when GPU is detected.
