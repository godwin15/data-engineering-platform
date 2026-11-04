
import os
from pathlib import Path
from minio import Minio

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9002")
MINIO_ACCESS_KEY = os.environ["MINIO_ROOT_USER"]
MINIO_SECRET_KEY = os.environ["MINIO_ROOT_PASSWORD"]

BUCKET_NAME = "wealth-management-bronze"
BRONZE_DIR = Path("data/bronze")

# Connect to MinIO
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


def upload_bronze_files():
    # Check that the Bronze directory exists
    if not BRONZE_DIR.exists():
        raise FileNotFoundError(
            f"Bronze directory not found: {BRONZE_DIR}"
        )

    # Create bucket if it doesn't exist
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")

    # Find all ORC files
    files = sorted(BRONZE_DIR.rglob("*.orc"))

    if len(files) != 210:
        raise ValueError(
            f"Expected 210 ORC files, found {len(files)}"
        )

    print(f"Found {len(files)} ORC files. Starting upload...\n")

    # Upload each ORC file
    for index, file_path in enumerate(files, start=1):

        # Preserve table/organization/date structure
        object_name = file_path.relative_to(
            BRONZE_DIR
        ).as_posix()

        client.fput_object(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            file_path=str(file_path),
            content_type="application/octet-stream"
        )

        if index % 25 == 0 or index == len(files):
            print(f"Uploaded {index}/{len(files)} files")

    # Verify uploaded objects
    uploaded_objects = list(
        client.list_objects(
            BUCKET_NAME,
            recursive=True
        )
    )

    uploaded_names = {
        obj.object_name
        for obj in uploaded_objects
        if obj.object_name.endswith(".orc")
    }

    expected_names = {
        file_path.relative_to(BRONZE_DIR).as_posix()
        for file_path in files
    }

    assert uploaded_names == expected_names, (
        "Uploaded files do not match local ORC files"
    )

    print("\nUpload completed successfully!")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Total ORC objects verified: {len(uploaded_names)}")


if __name__ == "__main__":
    upload_bronze_files()
