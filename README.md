# CSS Art & Video Generator

Converts images and video frames to pure CSS + HTML files using Breadth-first Search and Canny Edge Detection

![](github/sample.png)

## Tested on
 * Google Chrome
 * Brave Web Browser

## Tutorial
Install dependencies
```sh
$ apt update
$ apt install git python3-dev python3-pip ffmpeg
```

Clone repository
```sh
$ git clone https://github.com/kevinjycui/css-video.git
$ cd css-video
```

Install requirements
```sh
$ python -m venv env
$ . env/bin/activate
(env) $ pip install -r requirements.txt
```

Add an image file (PNG or JPG) or convert a video file into frames using FFmpeg (note frames should be named `frame%d.png` in which `%d` represents an index starting from 0)

eg. To convert a video `input.mp4` into frames with an FPS of 20 into a directory named `frames`:
```sh
(env) $ mkdir frames
(env) $ ffmpeg -i input.mp4 -vf fps=20 frames/frame%d.png
```

Run the converter

Image
```sh
(env) $ python3 generator.py -i input.png
```
Video
```sh
(env) $ python3 generator.py -f frames/
```