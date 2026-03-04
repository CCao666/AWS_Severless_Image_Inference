#!/bin/bash

set -e

echo "Building Pillow Lambda Layer..."

rm -rf python pillow-layer.zip
mkdir python

docker run --rm --platform linux/arm64 \
  --entrypoint /bin/bash \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.12 \
  -lc "pip install pillow -t python/"

zip -r pillow-layer.zip python

echo "Layer build complete: pillow-layer.zip"
