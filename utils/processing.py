from __future__ import annotations


def truncate_padding(sequence, max_length, sample_piece) -> list:
    """Truncate or pad a sequence to a fixed length."""
    if len(sequence) > max_length:
        sequence = sequence[:max_length]
    elif len(sequence) < max_length:
        sequence.extend([sample_piece] * (max_length - len(sequence)))
    return sequence


def normalize_bbox(bbox: tuple, width: int, height: int, scale: int = 1000) -> list:
    """Normalize bounding box coordinates to a 1000x1000 scale.

    Args:
        bbox (tuple): Bounding box coordinates in the format (x_min, y_min,
        x_max, y_max).
        width (int): Original width of the image.
        height (int): Original height of the image.
        scale (int): Range to normalize to.

    Returns:
        list: Normalized bounding box coordinates scaled to [0, 1000].
    """
    return [
        int(scale * (bbox[0] / width)),
        int(scale * (bbox[1] / height)),
        int(scale * (bbox[2] / width)),
        int(scale * (bbox[3] / height)),
    ]


def denormalize_boxes(box: tuple, width: int, height: int, scale: int = 1000) -> tuple:
    """Denormalize bounding box coordinates to original dimensions.

    Args:
        box (tuple): Normalized bounding box coordinates in the format
        [x_min, y_min, x_max, y_max].
        width (int): Original width of the image.
        height (int): Original height of the image.
        scale (int): Range to normalize to.

    Returns:
        tuple: Denormalized bounding box coordinates in the format
        (x_min, y_min, x_max, y_max).
    """
    x, y, x_max, y_max = box
    denorm_x_min = int(x * width / scale)
    denorm_y_min = int(y * height / scale)
    denorm_x_max = int(x_max * width / scale)
    denorm_y_max = int(y_max * height / scale)
    return denorm_x_min, denorm_y_min, denorm_x_max, denorm_y_max
