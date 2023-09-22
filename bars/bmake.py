import cv2
import qrcode
from qrcode.image.pure import PyPNGImage
from PIL import Image

def mbar(message:str, type='PIL', height=200, width=200, resize=False, **kwargs):
    code = qrcode.QRCode(**kwargs)
    code.add_data(message)
    if type == 'Pure':
        im = code.make_image(image_factory=PyPNGImage)
    elif type == 'PIL':
        im = code.make_image()
        code_width, code_height = im.size
        if ((code_width, code_height) != (width, height)) and resize:
            im = im.resize((width, height))
    else:
        raise TypeError
    
    return im

def qr_header(header_file, message="QR message", file="qrcode.png"):
  header = Image.open(header_file)
  header_width, header_height = header.size
  im = mbar(message)
  im.resize((header_height, header_height), Image.Resampling.LANCZOS)
  new = Image.new((header_width+header_height, header_height), mode=header.mode)
  new.paste(header, (0,0))
  new.paste(im, (header_width,0))
  new.save(file)
  
def embed_bar(bigim, smallim, xoff=0, yoff=0):
    bsh = bigim.shape
    ssh = smallim.shape
    xscale = 1. if bsh[0]-xoff-ssh[0] > 0 else ssh[0]/(bsh[0]-xoff)
    yscale = 1. if bsh[1]-yoff-ssh[1] > 0 else ssh[1]/(bsh[1]-yoff)
    if (xscale < 1) or (yscale < 1):
        sc = min(xscale, yscale)
        smallim = cv2.resize(smallim, (ssh[0]*sc, ssh[1]*sc, ssh[2]))
        ssh = smallim.shape
    newim = bigim
    newim[xoff : xoff + ssh[0], yoff : yoff + ssh[1], :] = smallim
    return newim

if __name__ == '__main__':
    im = cv2.imread('616944_orig.jpg')
    msg= 'u0testv0'
    bar = mbar(msg, border=2, box_size=6)
    print(type(bar))
    rb = bar.save(f'{msg}.png')
    print(dir(bar))
    newim = embed_bar(im, bar, im.shape[0]*.7, im.shape[1]*.6)
    cv2.imshow(newim)
    cv2.waitKey(0)
