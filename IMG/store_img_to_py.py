"""
    This file is used to store images in the PTB-BlueprintReader app.
"""

import base64
import os

if __name__ == '__main__':
    # 删除旧的
    if os.path.exists('ImgPng.py'):
        os.remove('ImgPng.py')
    with open('ImgPng.py', 'a') as f:
        f.write('"""This file is used to store images in the PTB-BlueprintReader app."""\n\n')
        # 只找images内的文件
        for file in os.listdir('ImgPng'):
            if file.endswith('.png'):
                with open(os.path.join('ImgPng', file), 'rb') as img:
                    img_base64 = base64.b64encode(img.read())
                    f.write(f'{file[:-4]} = {img_base64}\n\n')
    print('Done!')
