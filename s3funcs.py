# ============================================================
# 🪣 AWS S3 Bucket Operations in Google Colab
# ============================================================

# --- 1. Install & Import ---
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

print(Path(__file__).parent.absolute())
secrets_path = Path(__file__).parent / "resources" / "secrets.txt"

with open(secrets_path, "r") as f:
    lines = [line.strip() for line in f.readlines()]

AWS_ACCESS_KEY = lines[0]
AWS_SECRET_KEY = lines[1]
AWS_REGION     = lines[2]


# Create S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id     = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_KEY,
    region_name           = AWS_REGION
)

# ============================================================
# ✅ CREATE a Bucket
# ============================================================
def create_bucket(bucket_name, region="us-east-1"):
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"✅ Bucket '{bucket_name}' created successfully.")
    except ClientError as e:
        print(f"❌ Error creating bucket: {e}")


# ============================================================
# 📤 INSERT (Upload) a File into the Bucket
# ============================================================
def upload_file(bucket_name, local_file_path, s3_key=None):
    """
    local_file_path : path to the file on disk (or Colab /content/)
    s3_key          : name/path the file will have inside the bucket
                      (defaults to the filename)
    """
    if s3_key is None:
        s3_key = local_file_path.split("/")[-1]
    try:
        s3.upload_file(local_file_path, bucket_name, s3_key)
        print(f"✅ Uploaded '{local_file_path}' → s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"❌ Upload failed: {e}")

# ============================================================
# 📥 INSERT (Upload) Raw Content (without a local file)
# ============================================================
def put_object(bucket_name, s3_key, content):
    """content can be a str or bytes"""
    if isinstance(content, str):
        content = content.encode("utf-8")
    try:
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=content)
        print(f"✅ Object '{s3_key}' written to s3://{bucket_name}/")
    except ClientError as e:
        print(f"❌ put_object failed: {e}")

# ============================================================
# 📋 LIST all Objects in the Bucket
# ============================================================
def list_objects(bucket_name):
    try:
        resp = s3.list_objects_v2(Bucket=bucket_name)
        objects = resp.get("Contents", [])
        if not objects:
            print("🪣 Bucket is empty.")
        else:
            print(f"📋 Objects in '{bucket_name}':")
            for obj in objects:
                print(f"   • {obj['Key']}  ({obj['Size']} bytes)")
    except ClientError as e:
        print(f"❌ List failed: {e}")

# ============================================================
# 📥 DOWNLOAD a File from the Bucket
# ============================================================
def download_file(bucket_name, s3_key, local_path):
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"✅ Downloaded s3://{bucket_name}/{s3_key} → '{local_path}'")
    except ClientError as e:
        print(f"❌ Download failed: {e}")

# ============================================================
# 🗑️ REMOVE (Delete) a Specific Object from the Bucket
# ============================================================
def delete_object(bucket_name, s3_key):
    try:
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"✅ Deleted object '{s3_key}' from '{bucket_name}'.")
    except ClientError as e:
        print(f"❌ Delete object failed: {e}")

# ============================================================
# 🗑️ REMOVE Multiple Objects at Once (Batch Delete)
# ============================================================
def delete_objects_batch(bucket_name, s3_keys: list):
    objects = [{"Key": k} for k in s3_keys]
    try:
        resp = s3.delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": objects}
        )
        deleted = [d["Key"] for d in resp.get("Deleted", [])]
        print(f"✅ Batch deleted: {deleted}")
    except ClientError as e:
        print(f"❌ Batch delete failed: {e}")

# ============================================================
# 🪣 DELETE the Entire Bucket
# (Bucket must be empty first — this helper empties it too)
# ============================================================
def delete_bucket(bucket_name):
    try:
        # Empty the bucket first
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get("Contents", [])
            if objects:
                s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": [{"Key": o["Key"]} for o in objects]}
                )
        # Now delete the bucket itself
        s3.delete_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' and all its contents deleted.")
    except ClientError as e:
        print(f"❌ Delete bucket failed: {e}")