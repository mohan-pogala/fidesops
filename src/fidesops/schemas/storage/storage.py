import logging
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from fidesops.schemas.shared_schemas import FidesOpsKey
from pydantic import (
    Extra,
    ValidationError,
    root_validator,
    validator,
)
from pydantic.main import BaseModel

from fidesops.schemas.api import BulkResponse, BulkUpdateFailed

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Response formats"""

    json = "json"
    csv = "csv"


class FileNaming(Enum):
    """File naming options for data uploads"""

    request_id = "request_id"


class StorageDetails(Enum):
    """Enum for storage detail keys"""

    # s3-specific
    BUCKET = "bucket"
    OBJECT_NAME = "object_name"
    NAMING = "naming"
    MAX_RETRIES = "max_retries"
    # onetrust-specific
    SERVICE_NAME = "service_name"
    ONETRUST_POLLING_HR = "onetrust_polling_hr"
    ONETRUST_POLLING_DAY_OF_WEEK = "onetrust_polling_day_of_week"


class StorageDetailsOneTrust(BaseModel):
    """The details required to represent a OneTrust storage configuration."""

    service_name: str
    onetrust_polling_hr: int
    onetrust_polling_day_of_week: int

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class FileBasedStorageDetails(BaseModel):
    """A base class for all storage configuration that uses a file system."""

    naming: str = FileNaming.request_id.value  # How to name the uploaded file

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class StorageDetailsS3(FileBasedStorageDetails):
    """The details required to represent an AWS S3 storage bucket."""

    bucket: str
    object_name: str
    max_retries: Optional[int] = 0


class StorageDetailsLocal(FileBasedStorageDetails):
    """The details required to configurate local storage configuration"""


class StorageSecrets(Enum):
    """Enum for storage secret keys"""

    # s3-specific
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"
    # onetrust-specific
    ONETRUST_HOSTNAME = "onetrust_hostname"
    ONETRUST_CLIENT_ID = "onetrust_client_id"
    ONETRUST_CLIENT_SECRET = "onetrust_client_secret"


class StorageSecretsLocal(BaseModel):
    """A dummy schema for allowing any / no secrets for local filestorage."""

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.allow


class StorageSecretsS3(BaseModel):
    """The secrets required to connect to an S3 bucket."""

    aws_access_key_id: str
    aws_secret_access_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class StorageSecretsOnetrust(BaseModel):
    """The secrets required to send results back to Onetrust."""

    onetrust_hostname: str
    onetrust_client_id: str
    onetrust_client_secret: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class StorageType(Enum):
    """Enum for storage destination types"""

    s3 = "s3"
    gcs = "gcs"
    transcend = "transcend"
    onetrust = "onetrust"
    ethyca = "ethyca"
    local = "local"  # local should be used for testing only, not for processing real-world privacy requests


class StorageDestination(BaseModel):
    """Storage Destination Schema"""

    name: str
    type: StorageType
    details: Union[
        StorageDetailsS3,
        StorageDetailsOneTrust,
        StorageDetailsLocal,
    ]
    key: Optional[FidesOpsKey]
    format: Optional[ResponseFormat] = ResponseFormat.json.value  # type: ignore

    class Config:
        use_enum_values = True
        orm_mode = True

    @validator("details", pre=True, always=True)
    def validate_details(
        cls,
        v: Dict[str, str],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Custom validation logic for the `details` field.
        """
        storage_type = values.get("type")
        if not storage_type:
            raise ValueError("A `type` field must be specified.")

        try:
            schema = {
                StorageType.s3.value: StorageDetailsS3,
                StorageType.local.value: StorageDetailsLocal,
                StorageType.onetrust.value: StorageDetailsOneTrust,
            }[storage_type]
        except KeyError:
            raise ValueError(
                f"`storage_type` {storage_type} has no supported `details` validation."
            )

        try:
            schema.parse_obj(v)
        except ValidationError as exc:
            # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
            # so this exception is cast into a `ValueError`.
            errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
            raise ValueError(errors)

        return v

    @root_validator
    @classmethod
    def json_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Custom validation to ensure that OneTrust and local destination formats are valid.
        """
        json_only_destinations = [StorageType.onetrust.value, StorageType.local.value]
        storage_type = values.get("type")
        response_format = values.get("format")
        if (
            storage_type in json_only_destinations
            and response_format
            and response_format != ResponseFormat.json.value
        ):
            raise ValueError(
                "Only JSON upload format is supported for OneTrust and local storage destinations."
            )

        return values


class StorageDestinationResponse(BaseModel):
    """Storage Destination Response Schema"""

    name: str
    type: StorageType
    details: Dict[StorageDetails, Any]
    key: FidesOpsKey
    format: ResponseFormat

    class Config:
        orm_mode = True
        use_enum_values = True


class BulkPutStorageConfigResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of StorageConfig."""

    succeeded: List[StorageDestinationResponse]
    failed: List[BulkUpdateFailed]


SUPPORTED_STORAGE_SECRETS = Union[
    StorageSecretsS3,
    StorageSecretsOnetrust,
]
