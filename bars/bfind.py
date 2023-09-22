import cv2
import cv2.aruco as aruco # docs are at: https://docs.opencv.org/4.8.0/de/d67/group__objdetect__aruco.html 
import pypdf
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw, ImageFilter
from string import ascii_uppercase
from statistics import NormalDist
import zbar
import qreader

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.functional")

# CONSTANTS
QUADRANT = {(1, 1): 0.0, (-1, 1): 2 * np.pi, (-1, -1): np.pi, (1, -1): np.pi}
MAX_P_VALUE = 0.1

NoQRCode = RuntimeError("No QR Code Found")

# HELPER FUNCTIONS
def rect_from_pt_dxdy(pt: np.array, uh: float, uv: float):
    return np.array([pt + uv, pt + uv + uh, pt + uh, pt])

def atan(rise, run):
    return np.arctan(rise / run) + QUADRANT[(np.sign(rise), np.sign(run))]

def rescale_image(img: np.array, scale_factor: float) -> np.array:
    """Rescale the image by a given scale factor."""
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)
    dim = (width, height)
    return cv2.resize(img, dim, interpolation=cv2.INTER_LINEAR)

def detect_with_zbar(gray_img):
    scanner = zbar.Scanner()
    result = scanner.scan(gray_img)
    if result:
        for symbol in result:
            return symbol.data.decode(), symbol.position
    return None, None

def detect_with_qreader(imga):
    qrr = qreader.QReader()
    try:
        result = qrr.detect_and_decode(imga)
        print(f"QReader AI. got {result}")
        return result[0], None
    except:
        return None, None

def detect_with_cv2(imga):
    qr_code_detector = cv2.QRCodeDetector()
    qrc = qr_code_detector.detectAndDecode(imga)
    return qrc[0], qrc[1]

def detect_with_pyzbar(imga):
    decoded = decode(imga)
    if decoded:
        return decoded[0].data.decode(), None
    return None, None

def page_qr(img:Image, verbose = False):
    original_img = img.copy()

    for angle in [0, 175]:
        img = original_img.rotate(angle)
        imga = np.array(img)

        methods = [detect_with_zbar, detect_with_qreader, detect_with_cv2, detect_with_pyzbar]
        m_names = ["zbar", "qreader", "cv2", "pyzbar"]

        gray = cv2.cvtColor(imga, cv2.COLOR_RGB2GRAY) if len(imga.shape) > 2 else imga # convert to gray unless already gray
        for m_name, method in zip(m_names, methods):
            im = imga if m_name not in ["zbar"] else gray
            result, position = method(im)
            if not result:
                if verbose:
                    print(f"Rescaling {m_name}")
                result, position = method(rescale_image(im, 0.7))
            if result:
                if verbose:
                    print(f"success with method {m_name}. {result}")
                return True, (result, position, None)

    return False, (None, None, None)

BUBBLE_HEAD =  {"student" : {"items" : {"ID" : {(i, 0) : i for i in range(10)},
                    "SECTION" : {(19+2*i, 0) : 2*(1+i) for i in range(4)},
                    "FIRST_INIT" : {(i, 1 ) : ascii_uppercase[i] for i in range(26)},
                    "LAST_INIT"  : {(i, 2 ) : ascii_uppercase[i] for i in range(26)} },
                    "bounds" :  { "tl" : (0 , (np.max, np.min)), # top left
                                  "bl" : (1 , (np.max, np.max)), # bottom left
                                  "br" : (2 , (np.min, np.max)), # bottom right
                                  "tr" : (3 , (np.min, np.min))  # top right
                                  },
                    "grid" : (26, 3)
                            }
                }
class ArucoBubbleSheet:
    def __init__(self, q_items: dict = BUBBLE_HEAD, aruco_dict = aruco.DICT_4X4_50):
        self.q_items = q_items
        self.aruco_dict = aruco_dict

    def grid_from_rect(self, rect: np.array, nhoriz: int, nvert: int):
        gs = np.array([nhoriz, nvert])
#        print('--grid--')
#        print(gs)
#        for pt in rect:
#            print(pt)
#        print('--grid--')
        rect = np.array(rect)
        uh = (rect[3]-rect[0])/nhoriz  # horizontal unit vector. Shape = (2,)
        uv = (rect[1]-rect[0])/nvert   # vertical unit vector
#        print(f"({uh}) - ({uv})")
        grid = {(n, m) : rect_from_pt_dxdy(rect[0]+ uh*n + uv*m, uh, uv) for m in range(nvert) for n in range(nhoriz)}
        return grid

    def aruco_check_orientation(self, ad:dict, top_left:int=0, bottom_left:int=1, top_right:int=3, bottom_right:int=2):
        """ input: aruco dictionary from aruco detect. 
        top_left... = aruco index of each corner of the symbol
        """
        assert(all([i in ad for i in [top_right, top_left, bottom_right, bottom_left]])) # need to find / supply all 4 corners
        tl = ad[top_left][0] # aruco returns 4 corners of each box
        bl = ad[bottom_left][0]
        tr = ad[top_right][0]
        br = ad[bottom_right][0]
        pts = np.array([tr, tl, bl, br])
        ctr = np.array([pts[:,0].mean(), pts[:,1].mean()])
        vec = pts - ctr
        vr = vec[3] + vec[0]
        rot_angle = atan(vr[1], vr[0])
        angles = np.array([atan(pt[1],pt[0]) for pt in pts-ctr])
        print(f"orientation: angle list {180*angles/np.pi}. {angles.argsort()} | {rot_angle*180/np.pi}")
        return ( 180*rot_angle/np.pi, 1)

    def aruco_find(self, image: Image, verbose: bool = False): # **DetectorParameters are DetectorParameters
        """
        Find all aruco markers in the image.
        """
        a_param = aruco.DetectorParameters()
        ad = aruco.ArucoDetector(aruco.getPredefinedDictionary(self.aruco_dict), a_param)
        (corners, markers, rejected) = ad.detectMarkers(np.array(image))
        cr = [c[0] for c in corners]
        try:
            aruco_objects = {m[0]:c for m, c in zip(list(markers), cr)} 
        except TypeError:  # NoneType object is not iterable
            aruco_objects = {}
        return aruco_objects

    def box_from_bounds(self, bounds: np.array):
        x, y, w, h = cv2.boundingRect(bounds)
        return [x, y, x+w, y+h]

    def analyze_bubbles(self, img: Image, ad = None):
        """
        Analyze bubbles based on the provided q_items_template and grid dimensions.
        """
        q_items_list = self.q_items
        if ad is None:
            ad = self.aruco_find(np.array(img.image))
            (rot, flip) = self.aruco_check_orientation(ad)
            print(f"ORIENTATION rot, flip = {rot}, {flip}")
            image = img.image if flip == 1 else img.image[::-1,:,:]
            image = image.rotate(rot) # TODO: make rotation actually work!
            ad = self.aruco_find(np.array(image)) # re-find aruco after rotation
    #       image.show()
        else:
            try:
                image = img.image
            except AttributeError:
                image = img
        dr = ImageDraw.ImageDraw(image)
        ad_indices = set(ad.keys())
        # Initialize results dictionary based on q_items_template
        q_results = {section: {} for section, box in q_items_list.items() if box["set"] <= ad_indices}

        for section, q_items_template in q_items_list.items(): 
            if not q_items_template["set"].issubset(ad_indices):
                continue
            gb = q_items_template["bounds"]
            #  [ four [x,y] points to draw a rectangle around the bubble ]
            try:
                bubble_bounds = [[gb["tl"][1][0](ad[gb["tl"][0]][:,0]), gb["tl"][1][1](ad[gb["tl"][0]][:,1])], # gb[.][1][.] is a function that finds the desired value (max or min)
                             [gb["bl"][1][0](ad[gb["bl"][0]][:,0]), gb["bl"][1][1](ad[gb["bl"][0]][:,1])], # ad[] is a dictionary whose keys are aruco values and whose contents are a vector of box corners
                             [gb["br"][1][0](ad[gb["br"][0]][:,0]), gb["br"][1][1](ad[gb["br"][0]][:,1])],
                             [gb["tr"][1][0](ad[gb["tr"][0]][:,0]), gb["tr"][1][1](ad[gb["tr"][0]][:,1])]
                             ]
            except KeyError as ke:
                print(f"Section {section}, arUco code missing {ke}. Skipping to next section")
                q_results[section] = {name : {choice : 1 for choice in bubbles.values()} for name, bubbles in q_items_template["items"].items() }
                continue
            (grid_v, grid_h) = q_items_template["grid"]
            grid_boxes = self.grid_from_rect(bubble_bounds, grid_v, grid_h)
            boxctr = 0
            for box in grid_boxes.values():
                boxctr += 1
                dr.line(tuple(list(box.reshape(8,1))+list(box[0,:])), fill=(255,boxctr*2,255*(boxctr % 2)), width=5)
            boxsum = {k: np.array(image.crop(self.box_from_bounds(grid_boxes[k]))).sum() for k in grid_boxes.keys()}
    #       print(boxsum)

            for q_item_name, bubbles in q_items_template["items"].items():
                item_sum = np.array([boxsum[loc] for loc in bubbles.keys()])
                item_mean, item_std = np.mean(item_sum), np.std(item_sum)
                scores = {choice : (item_mean-boxsum[loc])/item_std for loc, choice in bubbles.items()} # z-scores
                scores = {k : 1-NormalDist().cdf(v) for k, v in scores.items()} #convert to p-values
                scores = dict(sorted(scores.items(), key=lambda item: item[1])) # sort p-values, low to high
                scores = {k: v for k,v in scores.items() if v < MAX_P_VALUE} # drop improbable results, NB gives empty dict if nothing is marked
                q_results[section][q_item_name] = scores
#        image.show()
        return q_results, image

class ArUcoGeneration:
    def __init__(self):
        pass

    @staticmethod
    def make_aruco_corners(fname_root=None, ftype='png', values=range(4), size=50):
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        corners = [aruco.generateImageMarker(aruco_dict, i, size) for i in values]
        if fname_root is not None:
            for v, im in zip(values, corners):
                fname = fname_root + str(v) + "." + ftype
                cv2.imwrite(fname, im)
        return corners

# MAIN TESTING AND DEMO
def demo_test():
    q_items =   {"student" : {"items" : {"ID" : {(i, 0) : i for i in range(10)},
                    "SECTION" : {(19+2*i, 0) : 2*(1+i) for i in range(4)},
                    "FIRST_INIT" : {(i, 1 ) : ascii_uppercase[i] for i in range(26)},
                    "LAST_INIT"  : {(i, 2 ) : ascii_uppercase[i] for i in range(26)} },
                    "bounds" :  { "tl" : (0 , (np.max, np.min)), # top left
                                  "bl" : (1 , (np.max, np.max)), # bottom left
                                  "br" : (2 , (np.min, np.max)), # bottom right
                                  "tr" : (3 , (np.min, np.min))  # top right
                                  },
                    "grid" : (26, 3)
                            },
                "self_assessment" : {"items" : {"score" : {(i, 0) : i+1 for i in range(10)}},
                                     "bounds" : { "tl" : (7 , (np.max, np.min)), # top left
                                                  "bl" : (7 , (np.max, np.max)), # bottom left
                                                  "br" : (8 , (np.min, np.max)), # bottom right
                                                  "tr" : (8 , (np.min, np.min)) }, # top right
                                     "grid" : (11, 1)
                                    },
                "assessment" : {"items" : {"score" : {(i, 0) : i+1 for i in range(10)}},
                                     "bounds" : { "tl" : (5 , (np.max, np.min)), # top left
                                                  "bl" : (5 , (np.max, np.max)), # bottom left
                                                  "br" : (6 , (np.min, np.max)), # bottom right
                                                  "tr" : (6 , (np.min, np.min)) }, # top right
                                     "grid" : (11, 1)
                                    },
                }
    sheet_reader = ArucoBubbleSheet(q_items)
    test_images = ["read_bubbles_bars_test3.pdf", "test_scan4_aruco.pdf","read_bubbles_bars_mp1.pdf"]
    pdfr = pypdf.PdfReader(test_images[2])
    print(f"\tProcessing {len(pdfr.pages)} pages:")
    for page in pdfr.pages:
        print(f"Found {len(page.images)} images on the first page")
        for i, img in enumerate(page.images):
            print(f"Page {i}: Type({type(img.image)}) in image {img.name}") # expect <class 'PIL.JpegImagePlugin.JpegImageFile'>, "Im1.jpg"
            qrc_success, qrc = page_qr(img.image)
            if not qrc_success:
                continue
            # qr_box = sheet_reader.box_from_bounds(qrc[1][0])
            aruco_sets = sheet_reader.aruco_find(img.image, verbose=True)
            print(f"Page {i} : {qrc[0]} : Detected {len(aruco_sets)} Aruco sets.")

            # For demonstration, we'll just use the first aruco set to analyze bubbles
            if aruco_sets:
                bubbles_data = sheet_reader.analyze_bubbles(img)
                for key, value in bubbles_data.items():
                    print(f"{key}:")
                    for k2, v2 in value.items():
                        print(f"    {k2} : {v2}")

if __name__ == '__main__':
    ArUcoGeneration.make_aruco_corners("aruco_test",values=[5, 6, 7, 8])
   # demo_test()
