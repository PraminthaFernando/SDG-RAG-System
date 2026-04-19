import boto3
import json
import os

BUCKET = os.getenv("AWS_BUCKET_NAME")

if not BUCKET:
    raise ValueError("AWS_BUCKET_NAME not set")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)


# =========================================================
# 🔥 UPLOAD
# =========================================================
def upload_llm_result(project_id: str, data: dict):
    key = f"llm-results/{project_id}.json"

    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(data, default=str),
            ContentType="application/json"
        )
        return key

    except Exception as e:
        print(f"[S3 ERROR] Upload failed: {e}")
        raise


# =========================================================
# 🔥 DOWNLOAD
# =========================================================
def get_llm_result_s3(key: str):
    try:
        res = s3.get_object(Bucket=BUCKET, Key=key)
        return json.loads(res["Body"].read().decode("utf-8"))

    except Exception as e:
        print(f"[S3 ERROR] Read failed: {e}")
        return None


# =========================================================
# 🔥 DELETE
# =========================================================
def delete_llm_result_s3(key: str):
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
    except Exception as e:
        print(f"[S3 ERROR] Delete failed: {e}")