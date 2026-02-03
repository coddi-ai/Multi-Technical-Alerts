"""
S3 Uploader for Oil Analysis Data Pipeline

Handles uploading Silver and Golden layer data to AWS S3.
"""

import boto3
from pathlib import Path
from typing import Optional
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

from src.utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class S3Uploader:
    """Handles uploading data to AWS S3."""
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.settings = get_settings()
        
        if not self._validate_credentials():
            logger.warning("S3 credentials not configured - uploads will be skipped")
            self.s3_client = None
            return
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.settings.access_key,
                aws_secret_access_key=self.settings.secret_key
            )
            logger.info(f"S3 client initialized for bucket: {self.settings.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _validate_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        return bool(
            self.settings.access_key and 
            self.settings.secret_key and 
            self.settings.bucket_name
        )
    
    def upload_file(
        self, 
        file_path: str | Path, 
        s3_key: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3.
        
        Args:
            file_path: Path to local file
            s3_key: S3 object key (path in bucket). If None, uses filename with prefix
        
        Returns:
            True if upload successful, False otherwise
        """
        if self.s3_client is None:
            logger.warning(f"S3 client not available - skipping upload of {file_path}")
            return False
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # Generate S3 key if not provided
        if s3_key is None:
            s3_key = f"{self.settings.aws_s3_prefix}{file_path.name}"
        
        try:
            logger.info(f"Uploading {file_path} to s3://{self.settings.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                str(file_path), 
                self.settings.bucket_name, 
                s3_key
            )
            
            file_size_kb = file_path.stat().st_size / 1024
            logger.info(f"✓ Successfully uploaded {file_path.name} ({file_size_kb:.2f} KB)")
            return True
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not available")
            return False
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials provided")
            return False
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return False
    
    def upload_silver_layer(self, client: str) -> bool:
        """
        Upload Silver layer data for a client.
        
        Args:
            client: Client name ('CDA' or 'EMIN')
        
        Returns:
            True if upload successful
        """
        silver_path = self.settings.get_silver_path(client)
        s3_key = f"{self.settings.aws_s3_prefix}silver/{client.upper()}.parquet"
        
        return self.upload_file(silver_path, s3_key)
    
    def upload_golden_layer(self, client: str) -> dict:
        """
        Upload all Golden layer files for a client.
        
        Args:
            client: Client name ('CDA' or 'EMIN')
        
        Returns:
            Dictionary with upload status for each file
        """
        results = {}
        
        # Upload classified reports
        classified_path = self.settings.get_classified_reports_path(client)
        s3_key = f"{self.settings.aws_s3_prefix}golden/{client.lower()}/classified.parquet"
        results['classified'] = self.upload_file(classified_path, s3_key)
        
        # Upload machine status
        machine_status_path = self.settings.get_machine_status_path(client)
        s3_key = f"{self.settings.aws_s3_prefix}golden/{client.lower()}/machine_status.parquet"
        results['machine_status'] = self.upload_file(machine_status_path, s3_key)
        
        # Upload Stewart Limits
        stewart_limits_path = self.settings.get_stewart_limits_path(client)
        s3_key = f"{self.settings.aws_s3_prefix}golden/{client.lower()}/stewart_limits.parquet"
        results['stewart_limits'] = self.upload_file(stewart_limits_path, s3_key)
        
        return results
    
    def upload_all_layers(self, client: str) -> dict:
        """
        Upload both Silver and Golden layers for a client.
        
        Args:
            client: Client name ('CDA' or 'EMIN')
        
        Returns:
            Dictionary with upload status for all files
        """
        logger.info(f"Uploading all layers for {client} to S3")
        
        results = {
            'client': client,
            'silver': self.upload_silver_layer(client),
            'golden': self.upload_golden_layer(client)
        }
        
        # Summary
        total_files = 1 + len(results['golden'])  # silver + golden files
        successful = sum([
            results['silver'],
            sum(results['golden'].values())
        ])
        
        logger.info(f"Upload complete for {client}: {successful}/{total_files} files uploaded successfully")
        
        return results


def upload_pipeline_outputs(client: str, upload_silver: bool = True, upload_golden: bool = True) -> dict:
    """
    Convenience function to upload pipeline outputs for a client.
    
    Args:
        client: Client name ('CDA' or 'EMIN')
        upload_silver: Whether to upload Silver layer
        upload_golden: Whether to upload Golden layer
    
    Returns:
        Dictionary with upload results
    """
    uploader = S3Uploader()
    results = {'client': client}
    
    if upload_silver:
        results['silver'] = uploader.upload_silver_layer(client)
    
    if upload_golden:
        results['golden'] = uploader.upload_golden_layer(client)
    
    return results
