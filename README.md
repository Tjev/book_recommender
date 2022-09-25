# Datasentics - Data Eng. Assignement

### Description
This repo contains the task assignement for DataSentics "Big Data Engineer" position.

## Usage

A build of the docker image from the provided Dockerfile is required first.
To build the image, make sure youre in the same directory as the Dockerfile and use the following:
```bash
docker build --rm -t datasentics-de-task .
```

Then simply run the `run_app.sh`.

The recommender app will be then available at `http://localhost:8501/`.