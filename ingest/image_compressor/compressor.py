import io
from PIL import Image
import logging
from ..util import convert_to_mime

_logger = logging.getLogger(__name__)
_compress_default_options = {
    "file_format": "jpg",
    "outputs": [
        {
            "quality": 85,
            "w": 250,
            "purpose": "thumbnail"
        },
        {
            "quality": 85,
            "w": 500,
            "purpose": "thumbnail"
        },
        {
            "quality": 85,
            "w": 750,
            "purpose": "preview"
        },
        {
            "quality": 85,
            "w": 1000,
            "purpose": "view"
        },
        {
            "quality": 85,
            "w": 2000,
            "purpose": "view"
        },
        {
            "quality": 85,
            "purpose": "view"
        }
    ]
}


def resize(image: Image.Image, width: int = None, height: int = None) -> Image.Image:
    """Resize an PIL Image object proportionally based on a given values
    If only either width or height is given, scales image proportionally.
    If both values are given ,resize image to the values
    If both values are not given, resizing does not occur

    Args:
        image (Image.Image): image to resize
        width (int): width of desired output image

    Returns:
        Image: Image.Image
    """
    old_size = image.size
    if width:
        if height:
            new_size = (width, height)
        else:
            new_size = (width, int(old_size[1] * (width / old_size[0])))
    elif height:
        if width:
            new_size = (width, height)
        else:
            new_size = (int(old_size[0] * (height / old_size[1])), height)
    else:
        return image

    _logger.debug(f"Resizing image to {new_size}")

    image = image.resize(new_size)
    return image


def save_io(image: Image.Image, img_format: str = "JPEG", quality: int = 85) -> io.BytesIO:
    """Saves an PIL Image to BytesIO

    Args:
        image (Image.Image): Source Image
        img_format (str, optional): Desired output format. Defaults to "JPEG".
        quality (int, optional): The Quality of JPG if using. Defaults to 85.

    Returns:
        io.BytesIO: A BytesIO of the saved / compressed image
    """

    img_format = img_format.upper()

    _logger.debug(f"Saving image as {img_format} as BytesIO")

    b = io.BytesIO()
    if img_format == "PNG":
        image.save(b, format="PNG", optimize=True)
    elif img_format == "JPG" or img_format == "JPEG":
        image.save(b, format="JPEG", quality=quality, optimize=True)

    b.seek(0)
    return b


def compress(image: Image.Image, options: dict = None) -> list:
    """Compress and resize a singe PIL image based on optiopns

    Args:
        image (Image.Image): Source Image
        options (dict, optional): Options to compress and resize the image, see _compress_default_option variable for example. Uses default options if None is given

    Returns:
        list: A list containg both output images and it's information such as size and format in tuple, (data: BytesIO, info: dict)
    """
    if options is None:
        options = _compress_default_options

    out_format = options["file_format"]
    out = []
    for out_options in options["outputs"]:
        out_img = image.copy()

        out_w = None
        out_h = None

        if "w" in out_options.keys():
            out_w = out_options["w"]

        if "h" in out_options.keys():
            out_h = out_options["h"]

        out_img = resize(out_img, out_w, out_h)
        out_b = save_io(out_img, out_format, out_options["quality"])
        out_info = {
            "width": out_img.size[0],
            "height": out_img.size[1],
            "content_type": convert_to_mime(out_format),
            "size_KB": int(out_b.getbuffer().nbytes / 1024),
            "purpose": out_options["purpose"]
        }
        out.append((out_b, out_info))

    return out

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("-q", "--quality", type=int,
#                         help="Quality setting of output image", default=85)
#     parser.add_argument("-x", "--resize", type=int,
#                         help="Output image x dimension size, scales y automatically")
#     parser.add_argument(
#         "-t", "--type", choices=["png", "jpg", "jpeg"], help="Output image format, can be either jpg or png",
#         default="jpg")
#     parser.add_argument(
#         "image", help="Source image location, can either be local or via http")
#     parser.add_argument(
#         "-d", "--use-s3", help="Use a S3 bucket as image source", metavar="BUCKET NAME", dest="bucket_download")
#     parser.add_argument("-u", "--upload-s3",
#                         help="Upload output image to a S3 bucket", metavar="BUCKET NAME", dest="bucket_upload")
#     parser.add_argument("-o", "--output", type=str,
#                         help="local location of output file, can be either a directory or filepath", metavar="OUTPUT")
#     args = parser.parse_args()

#     if args.bucket_download:
#         img = download_image_s3(args.bucket_download, args.image)
#     else:
#         img = Image.open(open(args.image, "rb"))

#     file_basename = os.path.basename(args.image)
#     file_extension = args.image.split(".")[-1].lower()

#     if file_extension == "png":
#         out_format = "PNG"
#     elif file_extension == "jpg":
#         out_format = "JPEG"
#     else:
#         out_format = "JPEG"

#     if args.resize:
#         img = resize(img, 1000)

#     if args.output:
#         if not os.path.exists(args.output):
#             raise FileNotFoundError()

#         if os.path.isfile(args.output):
#             save_file(img, args.output)
#         else:
#             save_file(img, f"{args.output}/{file_basename}")

#     if args.bucket_upload:
#         if args.type.upper() == "PNG" or out_format == "PNG":
#             out = save_io(img, "PNG")
#         else:
#             out = save_io(img, "JPEG", args.quality)
#         upload_s3(args.bucket_upload, out, file_basename, fmt=out_format)
