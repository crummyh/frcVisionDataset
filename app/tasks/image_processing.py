

import tarfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from PIL import Image as PIL_Image
from sqlmodel import Session

from app.core import config
from app.db.database import engine
from app.models.models import UploadStatus
from app.models.schemas import Image, UploadBatch
from app.services.buckets import create_image, get_upload_batch


async def process_batch_async(batch_id: UUID):

    with Session(engine) as session:

        def _update_batch_property(field: str, value):
            """
            Allows for changing single values of a batch
            without writing the entire "try, except, else"
            loop over and over
            """
            if not hasattr(batch, field):
                raise AttributeError(f"{type(batch).__name__} has no attribute '{field}'")

            try:
                setattr(batch, field, value)
            except Exception:
                session.rollback()
                raise
            else:
                session.commit()

        batch = session.get(UploadBatch, batch_id) # Get the batch
        if not batch:
            raise ValueError(f"UploadBatch with id {batch_id} not found")

        # Update the status and time to show that we have started
        _update_batch_property("status", UploadStatus.PROCESSING)
        _update_batch_property("start_time", datetime.now(timezone.utc))

        try:
            file = get_upload_batch(batch_id) # Get the actual file
            with tarfile.open(fileobj=file, mode="r:gz") as tar:
                image_files = [ # Get all the valid images in the archive
                    m for m in tar.getmembers()
                    if m.isfile()
                ]
                # Update the # of total images
                _update_batch_property("images_total", len(image_files))

                # Loop through every image
                for i, member in enumerate(image_files):
                    try:
                        if not _validate_image_pre(member):
                            _update_batch_property("images_rejected", batch.images_rejected + 1)
                            continue # Stop the loop here and start the next image

                        image = tar.extractfile(member) # Extract the image
                        assert image # The image has to exist

                        # Validate the image and add it to the database
                        if _validate_image(image):
                            image_entry = Image(
                                created_at=batch.capture_time,
                                created_by=batch.team,
                                batch=batch_id
                            )
                            session.add(image_entry)
                            session.flush()

                            image = _force_image_format(image)

                            assert image_entry.id # The ID is generated, so we assume it exists
                            create_image(image, image_entry.id) # Add the image to S3

                            # Increment the valid image count
                            _update_batch_property("images_valid", batch.images_valid + 1)

                        else:
                            # The image is not valid
                            _update_batch_property("images_rejected", batch.images_rejected + 1)

                    except Exception:
                        # Something went wrong somewhere, and the image is passed
                        _update_batch_property("images_rejected", batch.images_rejected + 1)
                        raise

            if batch.images_valid == 0:
                # If we made it through all images, but they
                # all failed, the batch is a failure.
                _update_batch_property("status", UploadStatus.FAILED)
            else:
                # but if at least some worked then we are done!
                _update_batch_property("status", UploadStatus.COMPLETED)

        except Exception as e:
            # Something went wrong, so we rollback say we failed
            session.rollback()
            _update_batch_property("status", UploadStatus.FAILED)
            _update_batch_property("error_message", str(e))
            raise
        else:
            session.commit()

def _force_image_format(image: BinaryIO) -> BytesIO:
    with PIL_Image.open(image) as img:
        output = BytesIO()
        img.save(output, format=config.IMAGE_STORAGE_FORMAT)
        output.seek(0)
        return output

def _validate_image(image_path: BinaryIO) -> bool:
    """Validate image meets requirements (640x640, etc.)"""
    try:
        with PIL_Image.open(image_path) as img:
            return img.size == (640, 640)
    except Exception:
        return False

def _validate_image_pre(image_member: tarfile.TarInfo) -> bool:
    """Validate image *before* extracting"""
    return Path(image_member.name).suffix.lower() in config.ALLOWED_IMAGE_EXTENSIONS

def estimate_upload_processing_time(session: Session, batch_id: UUID) -> float:
    """Estimate the time left in processing (in seconds)"""
    batch = session.get(UploadBatch, batch_id)
    if not batch:
        raise IndexError("batch id not found")

    if batch.status in {UploadStatus.COMPLETED, UploadStatus.FAILED}:
        return 0

    if batch.status == UploadStatus.UPLOADING:
        return config.DEFAULT_PROCESSING_TIME

    images_done = batch.images_valid + batch.images_rejected
    progress = images_done / batch.images_total
    assert batch.start_time
    delta_time = (batch.start_time - datetime.now(timezone.utc)).total_seconds()

    return (delta_time/progress)
