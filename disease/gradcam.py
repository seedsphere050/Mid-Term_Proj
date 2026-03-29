"""
gradcam.py - Auto-detects last Conv layer, works with any Keras model.
"""
import numpy as np
import cv2
import base64
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image as keras_image


def _find_last_conv_layer(model):
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    return None


def generate_gradcam(pil_img, model, class_index):
    try:
        layer_name = _find_last_conv_layer(model)
        if layer_name is None:
            print("[Grad-CAM] No Conv2D layer found.")
            return None
        print(f"[Grad-CAM] Using layer: {layer_name}")

        img = pil_img.convert("RGB").resize((224, 224))
        arr = keras_image.img_to_array(img)
        arr = np.expand_dims(arr, axis=0)
        arr = preprocess_input(arr.copy())

        grad_model = tf.keras.models.Model(
            inputs=[model.inputs],
            outputs=[model.get_layer(layer_name).output, model.output]
        )

        with tf.GradientTape() as tape:
            inputs = tf.cast(arr, tf.float32)
            conv_outputs, predictions = grad_model(inputs)
            loss = predictions[:, class_index]

        grads = tape.gradient(loss, conv_outputs)
        if grads is None:
            print("[Grad-CAM] Gradient is None.")
            return None

        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
        conv_out     = conv_outputs[0].numpy()

        for i in range(pooled_grads.shape[-1]):
            conv_out[:, :, i] *= pooled_grads[i]

        heatmap = np.mean(conv_out, axis=-1)
        heatmap = np.maximum(heatmap, 0)
        if heatmap.max() == 0:
            print("[Grad-CAM] Heatmap all zeros.")
            return None
        heatmap /= heatmap.max()

        heatmap_resized = cv2.resize(heatmap, (224, 224))
        heatmap_uint8   = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        original_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        superimposed  = cv2.addWeighted(original_bgr, 0.55, heatmap_colored, 0.45, 0)

        _, thresh = cv2.threshold(heatmap_uint8, 80, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 50:  # ignore tiny regions
                x, y, w, h = cv2.boundingRect(largest)

                pad = 10
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(223, x + w + pad), min(223, y + h + pad)

        # ✅ CHANGE 3: THICKER & MORE VISIBLE BOX
                cv2.rectangle(superimposed, (x1, y1), (x2, y2), (0, 255, 0), 4)

                cv2.putText(
                    superimposed,
                    "Disease Region",
                    (x1 + 5, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )

        _, buffer = cv2.imencode(".jpg", superimposed, [cv2.IMWRITE_JPEG_QUALITY, 92])
        b64 = base64.b64encode(buffer).decode("utf-8")
        print(f"[Grad-CAM] Success. b64 length: {len(b64)}")
        return f"data:image/jpeg;base64,{b64}"

    except Exception as e:
        print(f"[Grad-CAM] Exception: {type(e).__name__}: {e}")
        return None
