import magic
import base64

def file_path_mime(file_path):
    # https://medium.com/@ajrbyers/file-mime-types-in-django-ee9531f3035b
    mime = magic.from_file(file_path, mime=True)
    return mime

def check_in_memory_mime(in_memory_file):
    # https://medium.com/@ajrbyers/file-mime-types-in-django-ee9531f3035b
    mime = magic.from_buffer(in_memory_file.read(), mime=True)
    return mime

def image_field_response(image_field):
    data = image_field.file.read()
    data_base64 = base64.b64encode(data).decode('utf-8')
    mime_type = magic.from_buffer(data, mime=True)
    return {
        'data': data_base64,
        'mimeType': mime_type
    }
