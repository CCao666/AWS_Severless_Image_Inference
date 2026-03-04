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
## System Overview

This project implements a robust, event-driven image processing pipeline. It is designed to handle binary image data across two distinct execution paths, ensuring both flexibility for real-time requests and scalability for bulk uploads.

### Execution Flow

The system operates through two primary entry points:

1.  **Synchronous Path (REST API):**
    * A client sends a `POST` request to **Amazon API Gateway** with a reference to an existing S3 object.
    * API Gateway triggers the **Lambda Inference Engine**, which performs immediate classification and returns the result (label and confidence) in the HTTP response.
    * *Ideal for:* Real-time UI feedback and interactive applications.

2.  **Asynchronous Path (Event-Driven):**
    * A client uploads a raw image directly to the `/uploads` prefix of the **S3 Bucket**.
    * An **S3 Event Notification** automatically triggers the Lambda function.
    * The function processes the image in the background without requiring the client to wait.
    * *Ideal for:* Batch processing and high-throughput data ingestion.

### Core Logic & Transformation

Regardless of the trigger, the **Lambda Inference Engine** performs the following atomic operations:
* **Intelligence:** Calls **Amazon Rekognition** to identify "Cat" vs "Dog" labels.
* **Optimization:** Uses **Pillow** to resize and compress the image, saving storage costs and improving downstream loading speeds.
* **Persistence:** Writes a standardized record to **Amazon DynamoDB**, including a unique `request_id`, classification results, and processing latency for auditing.

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
