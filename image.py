import magic
import base64
import io

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def image_field_response(image_field):
    image_field.file.seek(0)
    data = image_field.file.read()
    data_base64 = base64.b64encode(data).decode('utf-8')
    mime_type = magic.from_buffer(data, mime=True)
    return {
        'data': data_base64,
        'mime_type': mime_type
    }

def create_thumbnail(image_field):
    from PIL import Image
    im = Image.open(image_field.file.name)
    width, height = im.size
    factor = max(width / 128, height / 128)
    resized = im.resize(
            (int(width / factor), int(height / factor))
        )

    buffer = io.BytesIO()
    resized.save(buffer, 'png')
    path = default_storage.save(
        f'{image_field.file.name.split(".")[0]}_thumb.png',
        ContentFile(buffer.getvalue())
    )
    return path

def save_pil_image(pil_image, filepath):
    buffer = io.BytesIO()
    pil_image.save(buffer, 'png')
    path = default_storage.save(
        filepath,
        ContentFile(buffer.getvalue())
    )
    return path
