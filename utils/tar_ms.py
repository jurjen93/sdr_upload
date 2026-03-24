import tarfile
from os import path

def tar_ms(ms_path):
    """
    Tar a file
    """
    output_filename = f"{ms_path}.tar"
    print(f"Archiving MeasurementSet: {ms_path}...")
    with tarfile.open(output_filename, "w") as tar:
        tar.add(ms_path, arcname=path.basename(ms_path))
    return output_filename
