# System Architecture

This document describes the technical architecture of the **Serverless Image Inference Pipeline** built on AWS.

The system processes images uploaded to Amazon S3, performs classification using Amazon Rekognition, resizes images using Pillow, and persists metadata in DynamoDB.

---

## 1. High-Level Architecture

The following diagram illustrates the serverless flow and service integration:

```mermaid
graph TD
    Client([Client / API]) -->|POST /predict| AGW[[API Gateway]]
    S3_Up[(S3: Uploads)] -->|S3 Event| Lambda{AWS Lambda}
    AGW --> Lambda
    
    subgraph "Inference & Processing"
        Lambda <--> Rek[Amazon Rekognition]
        Lambda --> S3_Proc[(S3: Processed)]
        Lambda --> DB[(Amazon DynamoDB)]
        Lambda -.-> CW[CloudWatch Logs]
    end
