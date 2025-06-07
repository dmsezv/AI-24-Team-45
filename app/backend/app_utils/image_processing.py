import cv2
import numpy as np
from loguru import logger


def read_image(file_bytes):
    """Decode image from bytes using OpenCV."""
    logger.info("Reading image from bytes")
    np_arr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image


def draw(img, res, allowed):
    if hasattr(res, "pandas"):
        for d in res.pandas().xyxy[0].to_dict("records"):
            label = d.get("name", str(d.get("class", "")))
            if allowed and label not in allowed:
                continue
            x1, y1, x2, y2 = map(int, (d["xmin"], d["ymin"], d["xmax"], d["ymax"]))
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{label} {d['confidence']:.2f}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
    else:
        r = res[0]
        boxes, names = r.boxes, r.names

        track_ids = boxes.id if boxes.id is not None else [None] * len(boxes)

        for xyxy, conf, cls_id, track_id in zip(
                boxes.xyxy, boxes.conf, boxes.cls, track_ids):

            label = names.get(int(cls_id), str(int(cls_id)))
            if allowed and label not in allowed:
                continue

            x1, y1, x2, y2 = map(int, xyxy)
            color = get_class_color(label)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            txt = f"{label} {conf:.2f}"
            if track_id is not None:
                txt += f" id:{int(track_id)}"

            cv2.putText(img, txt, (x1, y1-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)


def get_class_color(class_name):
    colors = {
        'car': (0, 255, 0),           # Зеленый
        'bus': (255, 0, 0),           # Синий
        'truck': (0, 165, 255),       # Оранжевый
        'motorcycle': (255, 0, 255),  # Пурпурный
        'bicycle': (0, 255, 255),     # Желтый
        'train': (128, 0, 128),       # Фиолетовый
        'ambulance': (0, 0, 255),     # Красный
        'person': (255, 255, 0),      # Голубой
    }

    if class_name not in colors:
        import random
        random.seed(hash(class_name))

        r = random.randint(100, 255)
        g = random.randint(100, 255) 
        b = random.randint(100, 255)

        return (b, g, r)

    return colors[class_name]
