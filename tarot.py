import os
import random
import streamlit as st
from PIL import Image
import numpy as np

# Classic Spreads
cols = st.columns(3)
cols = [x.empty() for x in cols]

files = os.listdir('./big')
files = [x for x in files if '_' not in x]
random.shuffle(files)

def open_image(fp):
    image = Image.open(fp)

    # 将图像转换为numpy数组
    image_array = np.array(image)

    # 创建180度顛倒的图像
    flipped_image = image.transpose(Image.ROTATE_180)
    flipped_image_array = np.array(flipped_image)

    return image_array, flipped_image_array

def pick_one():
    card_path = files.pop()
    img = open_image('./big/' + card_path)
    img_idx = random.choice([0, 1])
    return img[img_idx]

for col in cols:
    col.image('./cover_back.png')

if st.button('Go', use_container_width=True):
    for col in cols:
        img = pick_one()
        col.image(img)

