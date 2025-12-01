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


def upload_track_to_backblaze(audio_file, track_id, artist_name):
    """
    Upload audio track to Backblaze B2.
    Returns: Public URL or None if failed
    """
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    # Organize by artist
    sanitized_artist = artist_name.replace(' ', '_').lower()
    file_extension = pathlib.Path(audio_file.name).suffix
    key = f"tracks/{sanitized_artist}/{track_id}{file_extension}"
    
    # Guess content type
    content_type, _ = mimetypes.guess_type(audio_file.name)
    if not content_type:
        content_type = 'audio/mpeg'  # Default for MP3
    
    try:
        s3 = get_backblaze_client()
        
        # Upload with streaming support
        s3.upload_fileobj(
            audio_file,
            bucket,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',  # Cache for 1 year
                'ContentDisposition': 'inline'  # Allow streaming
            }
        )
        
        # Return public URL
        url = f"https://s3.us-east-005.backblazeb2.com/{bucket}/{key}"
        return url
        
    except ClientError as e:
        print(f"[UPLOAD ERROR] {e}")
        return None


def upload_cover_image_to_backblaze(image_file, track_id, artist_name):
    """
    Upload cover image to Backblaze B2.
    Returns: Public URL or None if failed
    """
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    sanitized_artist = artist_name.replace(' ', '_').lower()
    file_extension = pathlib.Path(image_file.name).suffix
    key = f"covers/{sanitized_artist}/{track_id}{file_extension}"
    
    content_type, _ = mimetypes.guess_type(image_file.name)
    if not content_type:
        content_type = 'image/jpeg'
    
    try:
        s3 = get_backblaze_client()
        
        s3.upload_fileobj(
            image_file,
            bucket,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',
                'ContentDisposition': 'inline'
            }
        )
        
        url = f"https://s3.us-east-005.backblazeb2.com/{bucket}/{key}"
        return url
        
    except ClientError as e:
        print(f"[UPLOAD ERROR] {e}")
        return None


def generate_presigned_stream_url(track_url, expiry=3600):
    """
    Generate presigned URL for streaming (optional, for private tracks).
    For public tracks, you can stream directly.
    """
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    # Extract key from URL
    if bucket in track_url:
        key = track_url.split(f"{bucket}/")[-1]
    else:
        return track_url
    
    try:
        s3 = get_backblaze_client()
        
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ResponseContentType': 'audio/mpeg',
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=expiry
        )
        return url
        
    except ClientError as e:
        print(f"[PRESIGN ERROR] {e}")
        return track_url


def delete_track_from_backblaze(track_url):
    """Delete track from Backblaze B2"""
    bucket = settings.BACK_BLAZE_BUCKET_NAME
    
    if bucket not in track_url:
        return False
    
    key = track_url.split(f"{bucket}/")[-1]
    
    try:
        s3 = get_backblaze_client()
        s3.delete_object(Bucket=bucket, Key=key)
        return True
        
    except ClientError as e:
        print(f"[DELETE ERROR] {e}")
        return False
    


# storage_utils.py

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

