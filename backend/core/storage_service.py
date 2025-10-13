"""
Storage service with local and S3 support
Auto-switches based on USE_S3 environment variable
"""
import os
import logging
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

logger = logging.getLogger(__name__)

# Configuration from environment
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "tulip-compliance-dev")
LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "uploads")

class StorageService:
    """Unified storage service that works with local filesystem or S3"""
    
    def __init__(self):
        self.use_s3 = USE_S3
        self.s3_bucket = S3_BUCKET
        self.local_dir = LOCAL_UPLOAD_DIR
        
        if self.use_s3:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.getenv("AWS_REGION", "us-east-1")
                )
                logger.info(f"S3 storage initialized for bucket: {self.s3_bucket}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                logger.info("Falling back to local storage")
                self.use_s3 = False
        else:
            logger.info(f"Using local storage at: {self.local_dir}")
    
    def save_file(self, tenant_id: str, file_obj: BinaryIO, filename: str) -> str:
        """
        Save file to storage (local or S3)
        
        Args:
            tenant_id: Tenant identifier for isolation
            file_obj: File-like object to save
            filename: Name of the file
            
        Returns:
            Path/URL to saved file
        """
        path = f"{tenant_id}/{filename}"
        
        try:
            if self.use_s3:
                # Upload to S3
                file_obj.seek(0)  # Reset file pointer
                self.s3_client.upload_fileobj(file_obj, self.s3_bucket, path)
                logger.info(f"File uploaded to S3: {path}")
                return f"s3://{self.s3_bucket}/{path}"
            else:
                # Save to local filesystem
                tenant_dir = Path(self.local_dir) / tenant_id
                tenant_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = tenant_dir / filename
                file_obj.seek(0)  # Reset file pointer
                
                with open(file_path, "wb") as f:
                    f.write(file_obj.read())
                
                logger.info(f"File saved locally: {file_path}")
                return str(file_path)
                
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    def get_file_url(self, tenant_id: str, filename: str) -> str:
        """
        Get URL/path for a stored file
        
        Args:
            tenant_id: Tenant identifier
            filename: Name of the file
            
        Returns:
            URL or path to file
        """
        if self.use_s3:
            return f"s3://{self.s3_bucket}/{tenant_id}/{filename}"
        else:
            return f"{self.local_dir}/{tenant_id}/{filename}"
    
    def read_file(self, tenant_id: str, filename: str) -> bytes:
        """
        Read file content from storage
        
        Args:
            tenant_id: Tenant identifier
            filename: Name of the file
            
        Returns:
            File content as bytes
        """
        try:
            if self.use_s3:
                path = f"{tenant_id}/{filename}"
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=path)
                return response['Body'].read()
            else:
                file_path = Path(self.local_dir) / tenant_id / filename
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise
    
    def delete_file(self, tenant_id: str, filename: str) -> bool:
        """
        Delete file from storage
        
        Args:
            tenant_id: Tenant identifier
            filename: Name of the file
            
        Returns:
            True if successful
        """
        try:
            if self.use_s3:
                path = f"{tenant_id}/{filename}"
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=path)
                logger.info(f"File deleted from S3: {path}")
            else:
                file_path = Path(self.local_dir) / tenant_id / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"File deleted locally: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

# Singleton instance
storage_service = StorageService()
