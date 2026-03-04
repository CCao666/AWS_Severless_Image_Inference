# System Architecture

This document describes the technical architecture of the **Serverless Image Inference Pipeline** built on AWS.

The system processes images uploaded to Amazon S3, performs classification using Amazon Rekognition, resizes images using Pillow, and persists metadata in DynamoDB.

---

## 1. High-Level Architecture

The following diagram illustrates the serverless flow and service integration:

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
