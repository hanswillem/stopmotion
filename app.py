#!/usr/bin/python3

# ---------------------------------------------------------------------------
# hotkeys
# ---------------------------------------------------------------------------
# ARROW_LEFT = next frame
# ARROW_RIGHT = previous frame
# ARROW_UP = fps + 1
# ARROW_DOWN = fps - 1
# SPACEBAR = play/stop image sequence
# ENTER = capture image
# F12 = ready for next capture
# BACKSPACE = delete image
# CTRL + E = export images
# CTRL + Z = undo delete last image
# CTRL + Q = quit
# ESCAPE = quit
# O = show/hide overlay image
# CTRL + O = remove all images (from disk) and start over
# ---------------------------------------------------------------------------

from picamera import PiCamera
import pygame
import os
from shutil import copyfile
from sys import argv

def getImages(p):
    l = []
    for i in os.listdir(p):
        ext = os.path.splitext(i)[1]
        if ext == '.png':
            l.append(os.path.join(p, i))
    l.sort()
    return l

def showImage(n):
    if anyImages():
        img = pygame.image.load(imgSeq[n])
        img = pygame.transform.scale(img, (w, h))
        win.blit(img, (0, 0))
    else:
        win.fill((0,0,0), [0, 0, w, h])

def anyImages():
    return len(imgSeq) > 0

def export():
    if anyImages():
        n = 0
        for i in imgSeq:
            sourceBasename = os.path.basename(i)
            sourceFilename = os.path.join(imgHiresPath, sourceBasename)
            exportFilename = os.path.join(imgExportPath, 'frame_' + '{:03d}'.format(n) + '.png')
            print(exportFilename)
            copyfile(sourceFilename, exportFilename)
            n += 1
        print('export finished!')

def deleteImagesFromDisk(*args):
    for i in args:
        for j in os.listdir(i):
            filename = os.path.join(i, j)
            if os.path.isfile(filename): 
                os.remove(filename)
                print('deleted ' + str(j))

def showHud():
    win.fill((200, 200, 200), [0, h, w, 30])
    # fps
    text_fps = font.render('fps: ' + str(fps), True, (0, 0, 0))
    win.blit(text_fps, [10, h + 5])
    # current frame
    if anyImages():
        text_currentFrame = font.render(str(imgIndex), True, (0, 0, 0))
        width_currentFrame = text_currentFrame.get_rect().width
        win.blit(text_currentFrame, [ (w / 2) - (width_currentFrame / 2), h + 5])
    else:
        text_noImages = font.render('NO IMAGES', True, (0, 0, 0))
        width_noImages = text_noImages.get_rect().width
        win.blit(text_noImages, [ (w / 2) - (width_noImages / 2), h + 5])

def startCam(o):
    if o:
        cam.start_preview(fullscreen = False, window = (320, 180 - 15, 1280, 720), alpha = 128)
    else:
        cam.start_preview(fullscreen = False, window = (320, 180 - 15, 1280, 720))

# setup picamera
cam = PiCamera()
#cam.resolution = (1640, 922)
cam.resolution = (1280, 720)
cam.framerate = 10
cam.vflip = True
cam.awb_mode = 'tungsten'

# center the window
os.environ['SDL_VIDEO_CENTERED'] = '1'

# setup pygame
pygame.init()
w = 1280
h = 720
hh = 30
win = pygame.display.set_mode((w, h + hh), pygame.NOFRAME)
pygame.display.set_caption('Stop Motion Machine')
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()
fps = 10
root = os.path.dirname(argv[0])
imgPath = os.path.join(root, 'img')
imgHiresPath = os.path.join(root, 'img_hires')
imgExportPath = os.path.join(root, 'export')
imgSeq = getImages(imgPath)
undo = None

if anyImages():
    imgIndex = len(imgSeq) - 1
    overlay = True
else:
    imgIndex = 0
    overlay = False

startCam(overlay)
livePreview = True
playing = False

# main loop
run = True
while run:
    showImage(imgIndex)
    showHud()

    if playing:
        if imgIndex == len(imgSeq) - 1:
            imgIndex = 0
        else:
            imgIndex += 1
        clock.tick(fps)

    # events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:

            # start/stop live preview
            if event.key == pygame.K_F12:
                    livePreview = True
                    playing = False
                    imgIndex = len(imgSeq) - 1
                    overlay = True
                    startCam(overlay)

            # capture image
            if event.key == pygame.K_RETURN:
                pygame.display.update()
                filenumber = len(imgSeq)
                # save lores image
                filename_lores = os.path.join(imgPath, 'capture_' + '{:03d}'.format(filenumber) + '.png')
                cam.capture(filename_lores, resize = (512, 288))
                # save hires image
                filename_hires = os.path.join(imgHiresPath, 'capture_' + '{:03d}'.format(filenumber) + '.png')
                cam.capture(filename_hires)

                if not anyImages():
                    overlay = True
                    startCam(overlay)

                # add image to sequence
                imgSeq.append(filename_lores)
                imgIndex = len(imgSeq) - 1

            # delete image
            if event.key == pygame.K_BACKSPACE:
                if anyImages():
                    livePreview = False
                    cam.stop_preview()
                    undo = [imgIndex, imgSeq[imgIndex]]
                    imgSeq.remove(imgSeq[imgIndex])
                    if imgIndex > (len(imgSeq) - 1):
                        imgIndex = len(imgSeq) - 1
                    if imgIndex == -1:
                        livePreview = True
                        overlay = False
                        startCam(overlay)
                        imgIndex = 0

            # start/stop playing
            if event.key == pygame.K_SPACE:
                if anyImages():
                    if playing:
                        playing = False
                    else:
                        playing = True
                        livePreview = False
                        cam.stop_preview()

            # navigate left
            if event.key == pygame.K_LEFT:
                if anyImages():
                    livePreview = False
                    cam.stop_preview()
                    if imgIndex > 0:
                        imgIndex -= 1

            # navigate right
            if event.key == pygame.K_RIGHT:
                if anyImages():
                    livePreview = False
                    cam.stop_preview()
                    if imgIndex < len(imgSeq) - 1:
                        imgIndex += 1
            # fps + 1
            if event.key == pygame.K_UP:
                fps += 1

            # fps - 1
            if event.key == pygame.K_DOWN:
                if fps > 0:
                    fps -= 1

            # undo
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if undo:
                    imgSeq.insert(undo[0], undo[1])
                    undo = None

            # delete all images from disk and start over
            if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                deleteImagesFromDisk(imgPath, imgHiresPath, imgExportPath)
                imgSeq.clear()
                imgIndex = 0
                overlay = False
                startCam(overlay)
                undo = None

            # reload all images from disk
            if event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                imgSeq.clear()
                imgSeq = getImages(imgPath)
                undo = None

            # quit
            if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                run = False
            if event.key == pygame.K_ESCAPE:
                run = False

            # start/stop overlay
            if event.key == pygame.K_o:
                if livePreview:
                    overlay = not overlay
                    startCam(overlay)

            # export
            if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                export()

    # update
    pygame.display.update()

pygame.quit()
quit()
