import numpy as np
import imagehash
from PIL import Image, ImageOps


# Gets the average hash, whash, phash, & dhash for each card in the set in each orientation for a total of 16 hashes
# Four different hash methods are used to reduce potential for error in using only one hashing method
class CardSet:
    def __init__(self):
        pass
    
    # Gets hashes of cards in set
    def getHashes(imageName,type):
        # Create an array with self.setSize rows and 4 columns. Each column represents a different hashing method
        arr = np.empty((1, 4), dtype=object)
        img = Image.open(imageName)
        match type:
            # For each case, find the average hash, whash, phash, & dhash of the image & convert it to a string
            case 'hash':  # Normally oriented card
                arr[0][0] = str(imagehash.average_hash(img))
                arr[0][1] = str(imagehash.whash(img))
                arr[0][2] = str(imagehash.phash(img))
                arr[0][3] = str(imagehash.dhash(img))
            case 'hashmir':  # Mirrored card
                imgmir = ImageOps.mirror(img)
                arr[0][0] = str(imagehash.average_hash(imgmir))
                arr[0][1] = str(imagehash.whash(imgmir))
                arr[0][2] = str(imagehash.phash(imgmir))
                arr[0][3] = str(imagehash.dhash(imgmir))
            case 'hashud':  # Upside down card
                imgflip = ImageOps.flip(img)
                arr[0][0] = str(imagehash.average_hash(imgflip))
                arr[0][1] = str(imagehash.whash(imgflip))
                arr[0][2] = str(imagehash.phash(imgflip))
                arr[0][3] = str(imagehash.dhash(imgflip))
            case 'hashudmir':  # Upside down & mirrored card
                imgmirflip = ImageOps.flip(ImageOps.mirror(img))
                arr[0][0] = str(imagehash.average_hash(imgmirflip))
                arr[0][1] = str(imagehash.whash(imgmirflip))
                arr[0][2] = str(imagehash.phash(imgmirflip))
                arr[0][3] = str(imagehash.dhash(imgmirflip))
        return arr
    
    
