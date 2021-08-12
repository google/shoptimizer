# Shoptimizer API Image Link Optimizer Guide

_Copyright 2021 Google LLC. This solution, including any related sample code or
data, is made available on an “as is,” “as available,” and “with all faults”
basis, solely for illustrative purposes, and without warranty or representation
of any kind. This solution is experimental, unsupported and provided solely for
your convenience. Your use of it is subject to your agreements with Google, as
applicable, and may constitute a beta feature as defined under those agreements.
To the extent that you make any data available to Google in connection with your
use of the solution, you represent and warrant that you have all necessary and
appropriate rights, consents and permissions to permit Google to use and process
that data. By using any portion of this solution, you acknowledge, assume and
accept all risks, known and unknown, associated with its usage, including with
respect to your deployment of any portion of this solution in your systems, or
usage in connection with your business, if at all._

## Overview

Image link optimizer validates the content of the imageLink and additionalImageLink fields. If both:
   * the image in imageLink is likely to be disapproved
   * at least one image in additionalImageLink is not likely to be disapproved
  then this swaps the imageLink URL with the best additionalImageLink URL.

## Requirements

This optimizer requires that both the imageLink and additionalImageLink fields are populated. Populating only imageLink will have no effect, as the optimizer requires at least 1 alternate additionalImageLink to swap the original image to if the primary is unsuitable.


## Processing

### Steps

  1. Validate URL formatting.
  2. If require_image_can_be_downloaded = True, download the image and perform checks on image file content.
  3. If require_image_score_quality_better_than is finite, score the downloaded image using a model.
  4. Swap images if desired.

### Parallelism

Each of the above steps is performed in sequence for each image (to the extent allowed by the configuration). Multiple images belonging to the same product are processed in parallel, provided there are sufficient processing threads available to the host system. Making additional processor threads available to the container will improve performance to a point, though keep in mind that network latency (for downloading images) is typically a greater factor in determining the speed of processing.

## Configuration

Configure this optimizer by editing `shoptimizer_api/config/image_link_optimizer_config.json`.

### `require_image_can_be_downloaded`

Type: boolean (true|false)
Default: true

* If True, image URLs must be accessible over the internet by this optimizer. The system (or container) running this optimizer must have internet access to download the images. Validates the file meets size requirements.
* If False, do not try to download any images. The images cannot be scored.

### `require_image_score_quality_better_than`

Type: float (0-inf)
Default: 0.9

Consider images likely to be disapproved if their quality score is worse than this value. The below guidelines apply to the default model included with Shoptimizer only:

| Value (float)      | Meaning               | Effect                                                                 |
|--------------------|-----------------------|------------------------------------------------------------------------|
| 0.0                | Best possible score.  | Always swap image with best alternate.                                 |
| 0 > value > 0.5    | Below par.            | Aggressively swap with alternate.                                      |
| 0.5 > value > 1.0  | Above par.            | Preferentially keep original image, but swap if the image is very poor |
| 1.0                | Worst possible score. | Swap only if the original violates policy (e.g. is inaccessible)       |
| Finite value > 1.0 | Impossibly poor score.| Swap only if the original violates policy (e.g. is inaccessible)       |
| inf                | Infinite score.       | Disable image scoring                                                  |
| Any negative value | None                  | Treat the same as 0                                                    |

Other notes:

* Image files with invalid or malformed content cannot be scored. The model will always try to swap these out for image files with valid content.
* The model cannot score TIFF images, even though they are accepted by GMC, so it will treat them as if the file content is malformed (as described above). The model will prefer non-TIFF images as a result, though other checks (e.g. for file size) will work as expected.

## Swap Logic

With the default settings, this optimizer will download and score all images on the imageLink and additionalImageLink fields. It will then mark images as "invalid" if they meet the following criteria (as per the [API documentation](https://support.google.com/merchants/answer/6324350)):

* The image URL is malformed.
* The image URL cannot be reached over the internet.
* The image file content is too large [>16MB].
* The image file content is not one of the allowed types [
JPEG (.jpg/.jpeg), WebP (.webp), PNG (.png), GIF (.gif), BMP (.bmp), and TIFF (.tif/.tiff)].
* The image scored below the threshold in `require_image_score_quality_better_than`, or otherwise cannot be scored.

If the imageLink image is "invalid", and at least one additionalImageLink image is not "invalid", then swap the URL on the imageLink field with the highest-scoring valid image URL in additionalimageLink.
