from PIL import Image
import numpy as np
import cv2

import cssutils
import bs4 as bs

import os
import sys
import getopt


VARIATION = 50
SIDELENGTH = 100
FPS = 20
DELAY = 15
BW_OPTIM = False # Turn on options to optimise for the Bad Apple!! PV specifically

def parse_args(argv):
    RUNCODE, SOURCE = 0, None
    try:
        opts, args = getopt.getopt(argv, 'hi:f:', ['image=', 'frames='])
    except getopt.GetoptError:
        print('Invalid arguments:\ngenerate.py -i <image>\ngenerate.py -f <frames>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Render image:\ngenerate.py -i <image>\nRender video from frames:\ngenerate.py -f <frames>')
            sys.exit()
        elif opt in ('-i', '--image'):
            if RUNCODE != 0:
                print('Invalid arguments: Must be strictly image or frames, cannot be both')
                sys.exit(2)
            RUNCODE = 1
            SOURCE = arg
        elif opt in ('-f', '--frames'):
            if RUNCODE != 0:
                print('Invalid arguments: Must be strictly image or frames, cannot be both')
                sys.exit(2)
            RUNCODE = 2
            SOURCE = arg
    return RUNCODE, SOURCE

def approx(px1, px2, var):
    return abs(px1[0] - px2[0]) <= var and abs(px1[1] - px2[1]) <= var and abs(px1[2] - px2[2]) <= var

def reduct(px): # Reduces colours to white, grey, black to optimise for the Bad Apple!! PV
    if px[0] < 100 and px[1] < 100 and px[2] < 100:
        return (0, 0, 0)
    elif px[0] > 155 and px[1] > 155 and px[2] > 155:
        return (255, 255, 255)
    return (125, 125, 125)

def get_polygons(filename, variation=VARIATION, bw_optim=BW_OPTIM):
    im = Image.open(filename)
    width, height = im.size

    if bw_optim:
        for i in range(width):
            for j in range(height):
                im.putpixel((i, j), reduct(im.getpixel((i, j))))

    rgb_im = im.convert('RGB')

    polygons = []

    visited = []

    for i in range(width):
        visited.append([False] * height)

    for i in range(width):
        for j in range(height):
            if not visited[i][j]:
                colour = rgb_im.getpixel((i, j))
                avg_colour = [colour[0], colour[1], colour[2], 1]

                arr_seg = np.zeros((height, width), np.float32)
                arr_seg.fill(255)

                pixels = 0
                
                queue = [(i, j)]
                arr_seg[j,i] = 0

                while len(queue) > 0:
                    x, y = queue.pop()
                    curr_colour = rgb_im.getpixel((x, y))
                    for rgb in range(3):
                        avg_colour[rgb] += curr_colour[rgb]
                    avg_colour[3] += 1

                    pixels += 1
        
                    if x-1 >= 0:
                        arr_seg[y,x-1] = 0
                        if not visited[x-1][y] and approx(rgb_im.getpixel((x-1, y)), colour, variation):
                            visited[x-1][y] = True
                            queue.append((x-1, y))
        
                    if x+1 < width:
                        arr_seg[y,x+1] = 0
                        if not visited[x+1][y] and approx(rgb_im.getpixel((x+1, y)), colour, variation):
                            visited[x+1][y] = True
                            queue.append((x+1, y))
        
                    if y-1 >= 0:
                        arr_seg[y-1,x] = 0
                        if not visited[x][y-1] and approx(rgb_im.getpixel((x, y-1)), colour, variation):
                            visited[x][y-1] = True
                            queue.append((x, y-1))
        
                    if y+1 < height:
                        arr_seg[y+1,x] = 0
                        if not visited[x][y+1] and approx(rgb_im.getpixel((x, y+1)), colour, variation):
                            visited[x][y+1] = True
                            queue.append((x, y+1))

                if pixels >= (6 if not bw_optim else 20):
                    rgb_im_seg = Image.fromarray(arr_seg).convert('RGB')
                    im_seg = cv2.cvtColor(np.array(rgb_im_seg), cv2.COLOR_RGB2BGR)

                    gray = cv2.cvtColor(im_seg, cv2.COLOR_BGR2GRAY)

                    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
                    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    # cv2.drawContours(im_seg, contours, -1, (0, 255, 0), 3)
                    # cv2.imshow('Contours', im_seg)
                    # cv2.waitKey(0)

                    # cv2.destroyAllWindows()

                    final_colour = (avg_colour[0]/avg_colour[3], avg_colour[1]/avg_colour[3], avg_colour[2]/avg_colour[3])

                    for contour in contours:
                        lst = contour.tolist()

                        points = []
                        for point in lst:
                            points.append(('%2f%%' % (100*point[0][0]/width), '%2f%%' % (100*point[0][1]/height)))

                        polygons.append((points, final_colour))

    return polygons

doc = '''
    <!DOCTYPE html>
    <html lang="en-US">
        <head>
            <meta charset="UTF-8">
            <meta content="Junferno" name="author"/>
            <title>CSS Video by Junferno</title>
            <link rel="stylesheet" href="style.css">
        </head>
        <body>
        </body>
    </html>'''

def write_polygons_image(filename):
    global doc

    polygons = get_polygons(filename)

    sheet = cssutils.css.CSSStyleSheet()

    soup = bs.BeautifulSoup(doc, 'html.parser')
    sheet.add('.component {width: %dvw; height: %dvw; position: absolute}' % (SIDELENGTH, SIDELENGTH))

    for i, polygon in enumerate(polygons):
        points, colour = polygon
        class_name = 'component-%d' % i

        sheet.add('.%s {clip-path: polygon(%s); background-color: rgb(%s)}' % (class_name, ','.join([x + ' ' + y for x, y in points]), ','.join(list(map(str, colour)))))

        tag = soup.new_tag('div')
        tag['class'] = 'component ' + class_name
        soup.body.append(tag)

    with open('result/index.html', 'w+') as f:
        f.write(str(soup))

    with open('result/style.css', 'w+') as f:
        f.write(sheet.cssText.decode('ascii'))

def write_polygons_video(dirname):
    global doc

    sheet = cssutils.css.CSSStyleSheet()

    soup = bs.BeautifulSoup(doc, 'html.parser')
    frames = len(os.listdir(dirname))

    sheet.add('.component {width: %dvw; height: %dvw; position: absolute; animation-duration: %.2fs; animation-delay: %.2fs}' % (SIDELENGTH, SIDELENGTH, frames/FPS, DELAY))

    keyframes = []

    for index in range(frames):
        polygons = get_polygons(dirname + '/frame%d.png' % (index + 1))

        prev_len = len(keyframes)

        if len(polygons) > prev_len:
            for j in range(prev_len, len(polygons)):
                class_name = 'component-%d' % j

                sheet.add('.%s {animation-name: play-%d}' % (class_name, j))

                tag = soup.new_tag('div')
                tag['class'] = 'component ' + class_name
                soup.body.append(tag)

                keyframes.append([])
        
        for i, polygon in enumerate(polygons):
            points, colour = polygon
            keyframes[i].append((round(100 * (index/frames), 2), ','.join([x + ' ' + y for x, y in points]), ','.join(list(map(str, colour)))))

        for i in range(len(polygons), len(keyframes)):
            keyframes[i].append((round(100 * (index/frames), 2),))

    for i in range(len(keyframes)):
        keyframe_css = '@keyframes play-%d {' % i
        if len(keyframes[i]) < frames:
            keyframe_css += '0% {clip-path: polygon(0% 0%); display: none}'
            pre = keyframes[i][0][0] - 100/frames
            if pre > 0:
                keyframe_css += '%.2f%% {clip-path: polygon(0%% 0%%); display: flex}' % pre
        
        empty_keyframe = ''
        hidden = False

        for component in keyframes[i]:
            if len(component) == 3:
                keyframe_css += empty_keyframe
                empty_keyframe = ''
                hidden = False
                keyframe_css += '%.2f%% {clip-path: polygon(%s); background-color: rgb(%s)}' % component
            elif not hidden:
                keyframe_css += '%.2f%% {clip-path: polygon(0%% 0%%)}' % component[0]
                hidden = True
            else:
                empty_keyframe = '%.2f%% {clip-path: polygon(0%% 0%%)}' % component[0]
        keyframe_css += '100% {clip-path: polygon(0% 0%)}}'
        sheet.add(keyframe_css)

    with open('result/index.html', 'w+') as f:
        f.write(str(soup))

    with open('result/style.css', 'w+') as f:
        f.write(sheet.cssText.decode('ascii'))

if __name__ == '__main__':
    RUNCODE, SOURCE = parse_args(sys.argv[1:])
    if RUNCODE == 1:
        write_polygons_image(SOURCE)
    elif RUNCODE == 2:
        write_polygons_video(SOURCE)
    else:
        print('Invalid arguments (must provide image file or video directory):\ngenerate.py -i <image>\ngenerate.py -f <frames>')
        sys.exit(2)