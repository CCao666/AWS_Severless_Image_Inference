# Serverless Cat vs Dog Image Inference (AWS)

A production-style **serverless computer vision pipeline** on AWS that classifies **cat vs dog** images using **Amazon Rekognition**, supports both **S3 event-driven inference** and **on-demand REST API** inference, and persists results to **DynamoDB**.

## Key Features

- **Cat vs Dog classification** using `rekognition:DetectLabels` with confidence scoring
- **Two inference modes**
  - **Async**: Upload an image to `s3://<bucket>/uploads/` → automatically triggers Lambda
  - **Sync**: Call `POST /predict` via API Gateway to run inference on an existing S3 object
- **Image preprocessing** with **Pillow (Lambda Layer)**: resize + JPEG compression, outputs to `processed/`
- **Metadata storage** in **DynamoDB**: prediction, confidence, latency, file size, request ID
- **Observability** via **CloudWatch Logs**
- **API protection** via `x-api-key` shared-secret authentication (prevents unauthorized calls)

---
