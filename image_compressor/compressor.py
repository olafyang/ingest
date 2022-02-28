from PIL import Image
import sys
import os
import re


args_pattern = r"((((?:-t|--type))\s(?P<TYPE>.*?)\s)?(((?:-q|--quality))\s(?P<QUAL>\d*?)\s)?(((?:-x|--resize))\s(?P<X>\d*?)\s)?(?P<IN>.*))"
out_type = ""
quality = 75
file_in = ""
file_out = ""
resize_x = 0

if __name__ == "__main__":
    try:
        match = re.match(args_pattern, " ".join(sys.argv[1:])).groupdict()
        out_type = match["TYPE"] if match["TYPE"] is not None else "jpg"
        quality = int(match["QUAL"]) if match["QUAL"] is not None else quality
        resize_x = int(match["X"]) if match["X"] is not None else None
        file_in = match["IN"]
        filename_clean = file_in.split(".")[-2].replace("/", "")
    except AttributeError:
        sys.stderr.write("Error in arguments")

    # Make new file name
    file_in = os.path.abspath(file_in)
    if resize_x:
        file_out = f"{os.path.split(file_in)[0]}/{filename_clean}-q{quality}-x{resize_x}.{out_type}"
    else:
        file_out = f"{os.path.split(file_in)[0]}/{filename_clean}-q{quality}.{out_type}"

    img = Image.open(file_in)

    if resize_x is not None:
        old_dimension = img.size
        scale = resize_x / old_dimension[0]
        new_dimension = (int(old_dimension[0] * scale), int(old_dimension[1] * scale))
        img = img.resize(new_dimension, Image.ANTIALIAS)

    img.save(file_out, quality=quality, optimize=True)
