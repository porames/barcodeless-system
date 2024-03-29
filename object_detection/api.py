import numpy as np
import os
import sys
import tensorflow as tf
from PIL import Image
from flask import Flask, jsonify, request
from io import BytesIO
import base64
from flask_cors import CORS, cross_origin
# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")


from utils import label_map_util
from utils import visualization_utils as vis_util

# What model to download.
MODEL_NAME = 'inno_inference_graph'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('data', 'object_detection.pbtxt')

NUM_CLASSES = 9
"""
opener = urllib.request.URLopener()
opener.retrieve('http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v1_coco_2017_11_17.tar.gz')
tar_file = tarfile.open('ssd_mobilenet_v1_coco_2017_11_17.tar.gz')
for file in tar_file.getmembers():
    file_name = os.path.basename(file.name)
    if 'frozen_inference_graph.pb' in file_name:
        tar_file.extract(file, os.getcwd())
"""
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)        
def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)

#PATH_TO_TEST_IMAGES_DIR = 'test_images'
#TEST_IMAGE_PATHS = [ os.path.join(PATH_TO_TEST_IMAGES_DIR, 'image2.jpg')]
#image_path = os.path.join('test_images', 'image1.jpg')
#imgurl = requests.get(url)
IMAGE_SIZE = (12, 8)
app = Flask(__name__)
CORS(app, support_credentials=True)
@cross_origin(supports_credentials=True)
@app.route('/api/alpha', methods=['POST','GET'])
def get_tasks():
    data = request.get_json()
    result = []
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            # Definite input and output Tensors for detection_graph
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
            detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')
            #for image_path in imgurl:
            image = Image.open(BytesIO(base64.b64decode(data['uri'])))
            # the array based representation of the image will be used later in order to prepare the
            # result image with boxes and labels on it.
            image_np = load_image_into_numpy_array(image)
            # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
            image_np_expanded = np.expand_dims(image_np, axis=0)
            # Actual detection.
            (boxes, scores, classes, num) = sess.run(
                [detection_boxes, detection_scores, detection_classes, num_detections],
                feed_dict={image_tensor: image_np_expanded})
            # Visualization of the results of a detection.
            vis_util.visualize_boxes_and_labels_on_image_array(
                image_np,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,
                line_thickness=8)
            #plt.figure(figsize=IMAGE_SIZE)
            #plt.imshow(image_np)
            j = 0
            for i in classes[0]:
                if scores[0][j] > 0.5:
                    name = category_index.get(i)["name"]
                    ymin = float(boxes[0][j][0])
                    xmin = float(boxes[0][j][1])
                    ymax = float(boxes[0][j][2])
                    xmax = float(boxes[0][j][3])                
                    score = float(scores[0][j])
                    result.append({"item":name,"score": score, "xmax": xmax, "xmin": xmin, "ymax": ymax, "ymin": ymin})
                j=j+1
    #result.headers.add('Access-Control-Allow-Origin', '*')
    print(result)
    return jsonify({'result':result})
    
if __name__ == '__main__':
    app.run(debug=True)