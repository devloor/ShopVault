import zlib
import struct
from pathlib import Path

BASE = Path('static')
BASE.mkdir(parents=True, exist_ok=True)

def write_png(path, size, color):
    width, height = size
    raw = b''
    for _ in range(height):
        raw += b'\x00' + bytes(color) * width
    compressor = zlib.compressobj()
    data = compressor.compress(raw) + compressor.flush()

    def chunk(c_type, data_bytes):
        chunk_data = struct.pack('>I', len(data_bytes)) + c_type + data_bytes
        chunk_data += struct.pack('>I', zlib.crc32(c_type + data_bytes) & 0xFFFFFFFF)
        return chunk_data

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', data)
    png += chunk(b'IEND', b'')
    path.write_bytes(png)

write_png(BASE / 'favicon.png', (64, 64), (255, 153, 0))
write_png(BASE / 'apple-touch-icon.png', (180, 180), (255, 153, 0))
print('written icons to', BASE)
