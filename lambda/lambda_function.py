import json
import os
import time
import urllib.parse
from datetime import datetime, timezone
from io import BytesIO

import boto3
from PIL import Image  # from your Pillow layer

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
rek = boto3.client("rekognition")

TABLE_NAME = os.environ.get("TABLE_NAME", "ImageInferenceResults")
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "processed/")
RESIZE_MAX = int(os.environ.get("RESIZE_MAX", "512"))

def classify_from_labels(labels: list[dict]) -> dict:
    name_to_conf = {x["Name"].lower(): float(x.get("Confidence", 0.0)) for x in labels}
    cat_conf = max([v for k, v in name_to_conf.items() if k in ("cat", "kitten", "feline")] + [0.0])
    dog_conf = max([v for k, v in name_to_conf.items() if k in ("dog", "puppy", "canine")] + [0.0])

    if cat_conf >= 60.0 and cat_conf >= dog_conf:
        return {"class": "cat", "confidence": cat_conf}
    if dog_conf >= 60.0 and dog_conf > cat_conf:
        return {"class": "dog", "confidence": dog_conf}
    return {"class": "other", "confidence": max(cat_conf, dog_conf)}

def resize_to_jpeg(img_bytes: bytes, max_side: int) -> bytes:
    with Image.open(BytesIO(img_bytes)) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = min(max_side / max(w, h), 1.0)  # do not upscale
        new_w, new_h = int(w * scale), int(h * scale)

        if (new_w, new_h) != (w, h):
            im = im.resize((new_w, new_h))

        out = BytesIO()
        im.save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()

def lambda_handler(event, context):
    # If this is an API Gateway / Function URL request
    if isinstance(event, dict) and ("requestContext" in event or "rawPath" in event or "httpMethod" in event):
        api_key = os.environ.get("API_KEY")

        headers = event.get("headers", {})
        provided_key = headers.get("x-api-key") or headers.get("X-Api-Key")

        if api_key and provided_key != api_key:
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unauthorized"})
            }
        try:
            body = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                import base64
                body = base64.b64decode(body).decode("utf-8")
            payload = json.loads(body)
        except Exception:
            payload = {}

        bucket = payload.get("bucket")
        key = payload.get("key")

        if not bucket or not key:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'bucket' and/or 'key' in JSON body"})
            }

        # Run single-object pipeline
        item = run_pipeline_for_one_object(bucket=bucket, key=key, context=context)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(item)
        }

    # Otherwise assume S3 event
    table = ddb.Table(TABLE_NAME)
    records = event.get("Records", [])
    results = []

    for r in records:
        bucket = r["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])
        item = run_pipeline_for_one_object(bucket=bucket, key=key, context=context, event_time=r.get("eventTime"))
        results.append(item)

    return {"statusCode": 200, "body": json.dumps({"written": len(results), "items": results})}


def run_pipeline_for_one_object(bucket: str, key: str, context, event_time: str | None = None) -> dict:
    t0 = time.time()
    table = ddb.Table(TABLE_NAME)
    event_time = event_time or datetime.now(timezone.utc).isoformat()

    # 1) Rekognition inference
    resp = rek.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}}, MaxLabels=20)
    labels = resp.get("Labels", [])
    pred = classify_from_labels(labels)

    # 2) Download image
    obj = s3.get_object(Bucket=bucket, Key=key)
    img_bytes = obj["Body"].read()
    input_bytes = len(img_bytes)

    # 3) Resize + upload processed image
    resized_bytes = resize_to_jpeg(img_bytes, RESIZE_MAX)
    base = key.split("/")[-1].rsplit(".", 1)[0]
    processed_key = f"{PROCESSED_PREFIX}{base}_{RESIZE_MAX}.jpg"

    s3.put_object(Bucket=bucket, Key=processed_key, Body=resized_bytes, ContentType="image/jpeg")

    latency_ms = int((time.time() - t0) * 1000)

    item = {
        "pk": f"s3://{bucket}/{key}",
        "sk": event_time,
        "bucket": bucket,
        "key": key,
        "processed_key": processed_key,
        "pred_class": pred["class"],
        "confidence": str(pred["confidence"]),
        "input_bytes": input_bytes,
        "latency_ms": latency_ms,
        "model_source": "rekognition.detect_labels",
        "request_id": context.aws_request_id,
    }
    table.put_item(Item=item)

    print(json.dumps({"pk": item["pk"], "pred": item["pred_class"], "processed_key": processed_key, "latency_ms": latency_ms}))
    return item
