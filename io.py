import magic
import base64

def image_field_response(image_field):
    data = image_field.file.read()
    data_base64 = base64.b64encode(data).decode('utf-8')
    mime_type = magic.from_buffer(data, mime=True)
    return {
        'data': data_base64,
        'mimeType': mime_type
    }
