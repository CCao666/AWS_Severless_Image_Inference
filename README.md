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
## Architecture

```mermaid
graph TD
    %% Nodes
    Client([Client / User])
    AGW[[API Gateway]]
    Lambda{AWS Lambda<br/>Inference Engine}
    Rek[Amazon Rekognition]
    DB[(Amazon DynamoDB)]
    S3_Up[(S3: uploads/)]
    S3_Proc[(S3: processed/)]
    CW[CloudWatch Logs]

    %% Styles
    classDef aws fill:#f90,stroke:#232F3E,stroke-width:2px,color:#fff;
    classDef storage fill:#3F8624,stroke:#232F3E,stroke-width:2px,color:#fff;
    classDef logic fill:#D05C17,stroke:#232F3E,stroke-width:2px,color:#fff;
    
    class AGW,Lambda logic;
    class S3_Up,S3_Proc,DB storage;
    class Rek aws;

    %% Async Path
    Client -->|1. Upload Image| S3_Up
    S3_Up -->|2. S3 Event Trigger| Lambda

    %% Sync Path
    Client -->|1. POST /predict| AGW
    AGW -->|2. Invoke| Lambda

    %% Internal Logic
    Lambda <-->|3. DetectLabels| Rek
    Lambda -->|4. Resize & Compress| S3_Proc
    Lambda -->|5. Persist Metadata| DB
    Lambda -.->|Logs & Metrics| CW

    %% Layout Arrangement
    subgraph "AWS Cloud (Serverless Stack)"
        AGW
        Lambda
        Rek
        S3_Up
        S3_Proc
        DB
        CW
    end
```
