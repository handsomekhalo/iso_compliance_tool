# storage_utils.py
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import mimetypes
import pathlib


def get_backblaze_client():
    """Get configured Backblaze B2 client"""
    return boto3.client(
        's3',
        endpoint_url='https://s3.us-east-005.backblazeb2.com',
        aws_access_key_id=settings.BACK_BLAZE_KEY_ID,
        aws_secret_access_key=settings.BACK_BLAZE_APLLICATION_KEY,
        region_name='us-east-005'
    )


# ADD this new function to your existing file:

def upload_iso_xml_to_backblaze(xml_file, bank_id, filename):
    """
    Upload ISO 20022 XML file to Backblaze B2.
    
    Args:
        xml_file: File object or BytesIO
        bank_id: Bank identifier for folder organization
        filename: Original filename
    
    Returns: 
        tuple: (public_url, file_hash, file_size) or (None, None, None) if failed
    """
    import hashlib
    
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    # Organize by bank
    key = f"iso_files/bank_{bank_id}/{filename}"
    
    try:
        # Calculate hash and size before upload
        xml_file.seek(0)  # Reset file pointer
        file_content = xml_file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
        
        # Reset pointer for upload
        xml_file.seek(0)
        
        s3 = get_backblaze_client()
        
        # Upload XML file
        s3.upload_fileobj(
            xml_file,
            bucket,
            key,
            ExtraArgs={
                'ContentType': 'application/xml',
                'CacheControl': 'max-age=2592000',  # Cache for 30 days
                'ContentDisposition': f'attachment; filename="{filename}"',  # Force download
                'Metadata': {
                    'bank_id': str(bank_id),
                    'file_hash': file_hash
                }
            }
        )
        
        # Return public URL
        url = f"https://s3.us-east-005.backblazeb2.com/{bucket}/{key}"
        return url, file_hash, file_size
        
    except ClientError as e:
        print(f"[ISO XML UPLOAD ERROR] {e}")
        return None, None, None
    except Exception as e:
        print(f"[UNEXPECTED UPLOAD ERROR] {e}")
        return None, None, None



def open_iso_xml_in_backblaze(filepath):
    """
    Generates a presigned URL for an ISO XML file stored on Backblaze B2 for inline viewing.
    
    Args:
        filepath: Full URL or key of the file in Backblaze
    
    Returns:
        str: Presigned URL or original filepath if error occurs
    """
    import pathlib
    from botocore.exceptions import ClientError
    
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    s3 = get_backblaze_client()

    # Normalize filepath to extract key
    filepath_str = str(filepath)
    if filepath_str.startswith("http") and bucket in filepath_str:
        key = filepath_str.split(f"{bucket}/")[-1]
    elif bucket not in filepath_str:
        key = filepath_str
    else:
        key = filepath_str.split(f"{bucket}/")[-1]

    # Content type for XML
    content_type = "application/xml"

    # Check if file exists
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print(f"[HEAD ERROR] {e}")
        return filepath_str  # Return original if file not found

    # Generate presigned URL
    try:
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ResponseContentDisposition': 'inline',
                'ResponseContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        return url
    except ClientError as e:
        print(f"[PRESIGN ERROR] {e}")
        return filepath_str


def delete_iso_xml_from_backblaze(file_url):
    """
    Delete ISO XML file from Backblaze B2
    
    Args:
        file_url: Full URL of the file to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    if bucket not in file_url:
        return False
    
    # Extract key from URL
    key = file_url.split(f"{bucket}/")[-1]
    
    try:
        s3 = get_backblaze_client()
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"[DELETED] {key}")
        return True
        
    except ClientError as e:
        print(f"[DELETE ERROR] {e}")
        return False

