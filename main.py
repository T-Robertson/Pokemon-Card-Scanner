import cv2
import numpy as np
import utils
import CardSet
from PIL import Image, ImageOps
import time
import playsound

class PokemonCardScanner:
    def __init__(self):
        # Initialize card set hashes dictionary
        self.cardsearchhashs = {}
        
        # Cards collected
        self.collectedCards = {}
        self.totalCardsCollected = 0
        
        #start main function
        self.main()
        
    def main(self):
        self.generateCardSetHashes() 
        print("Card set hashes generated.")
        #print(self.cardsearchhashs)  # For testing: print the generated card set hashes
        print("Starting card reader...")
        self.readCard()
        
    def readCard(self):
        rotateCamFeed = True        # Flag signaling if images are being read live from phone camera or from image file
        cam = cv2.VideoCapture(0)   # 0 = computer webcam

        # Scaled to the IRL height and width of a Pokemon card (6.6 cm x 8.8 cm)
        widthCard = utils.getWidthCard()
        heightCard = utils.getHeightCard()
        lastmatchingCard = cv2.resize(cv2.imread('CardsImages/001.jpg'), (widthCard, heightCard))# Set lastmatchingCard to a blank image to start; will be updated when a card is found

        while True:
            # Create a blank image
            blackImg = np.zeros((heightCard, widthCard, 3), np.uint8)

            # Check if using phone camera or saved picture
            if rotateCamFeed:
                # Read in frame and rotate 90 degrees b/c video comes in horizontally
                check, frame = cam.read()
                rot90frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                rot90frame = cv2.resize(rot90frame, (widthCard, heightCard))

            # Make image gray scale
            grayFrame = cv2.cvtColor(rot90frame, cv2.COLOR_BGR2GRAY)
            # Blur the image to reduce noise
            blurredFrame = cv2.GaussianBlur(grayFrame, (3, 3), 0)

            # Use Canny edge detection to get edges
            edgedFrame = cv2.Canny(image=blurredFrame, threshold1=100, threshold2=200)

            # Clean up edges
            kernel = np.ones((5,5))
            frameDial = cv2.dilate(edgedFrame, kernel, iterations=2)
            frameThreshold = cv2.erode(frameDial, kernel, iterations=1)

            # Get image contours
            contourFrame = rot90frame.copy()
            bigContour = rot90frame.copy()
            contours, hierarchy = cv2.findContours(frameThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(contourFrame, contours, -1, (0, 255, 0), 10)

            imgWarpColored = blackImg  # Set imgWarpColored
            # Get biggest contour
            corners, maxArea = utils.biggestContour(contours)
            if len(corners) == 4:
                corners = [corners[0][0], corners[1][0], corners[2][0], corners[3][0]]
                corners = utils.reorderCorners(corners)  # Reorders corners to [topLeft, topRight, bottomLeft, bottomRight]
                #cv2.drawContours(bigContour, corners, -1, (0, 255, 0), 10)
                bigContour = utils.drawRectangle(bigContour, corners)
                pts1 = np.float32(corners)
                pts2 = np.float32([[0, 0], [widthCard, 0], [0, heightCard], [widthCard, heightCard]])
                # Makes a matrix that transforms the detected card to a vertical rectangle
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                # Transforms card to a rectangle widthCard x heightCard
                imgWarpColored = cv2.warpPerspective(rot90frame, matrix, (widthCard, heightCard))

            # Resize all of the images to the same dimensions
            # Note: imgWarpColored is already resized and matchingCard gets resized in utils.getMatchingCard()
            rot90frame = cv2.resize(rot90frame, (widthCard, heightCard))
            grayFrame = cv2.resize(grayFrame, (widthCard, heightCard))
            blurredFrame = cv2.resize(blurredFrame, (widthCard, heightCard))
            edgedFrame = cv2.resize(edgedFrame, (widthCard, heightCard))
            contourFrame = cv2.resize(contourFrame, (widthCard, heightCard))
            bigContour = cv2.resize(bigContour, (widthCard, heightCard))

            # An array of all 7 images
            imageArr = ([rot90frame, grayFrame, blurredFrame, edgedFrame],
                        [contourFrame, bigContour, imgWarpColored, lastmatchingCard])

            # Labels for each image
            labels = [["Original", "Gray", "Blurred", "Threshold"],
                    ["Contours", "Biggest Contour", "Warped Perspective", "Last Matching Card"]]

            # Stack all 8 images into one and add text labels
            stackedImage = utils.makeDisplayImage(imageArr, labels)

            # Display the image
            cv2.imshow("Card Finder", stackedImage)
            
            # If the warped image is not blank, we have found a card and can check if it's a card in our set
            if imgWarpColored is not blackImg:
                # Check if a matching card has been found, and if so, display it
                matchingCard = utils.findCard(imgWarpColored, self.cardsearchhashs)
                if matchingCard is not None:
                    print("Matching card found!")
                    print(matchingCard)  # For testing: print the matching card info
                    lastmatchingCard = cv2.resize(cv2.imread('CardsImages/' + str(matchingCard).rjust(3, '0') + '.jpg'), (widthCard, heightCard))
                    #add function to ensure that the same card isn't counted multiple times in a row here
                    self.totalCardsCollected += 1
                    self.collectedCards.update({matchingCard: self.collectedCards.get(matchingCard, 0) + 1})  # Add matching card to collected cards
                    print(self.collectedCards)
                    #add function to action matching card here
                    playsound.playsound(sound="Collect.wav")# Play sound when card is found
                    #wait to see what to do with matching card
                    time.sleep(1)
                    #break
            
            if cv2.waitKey(1) & 0xFF == ord('q'):  # If reading from video, quit if 'q' is pressed
                print("Stopping card reader...")
                #Print text file of collected cards
                with open('collectedCards.txt', 'w') as f:
                    f.write(f"Collected Cards: {time.ctime()}\n")
                    f.write(f"Total Cards Collected: {sum(self.collectedCards.values())}\n")
                    for card, count in sorted(self.collectedCards.items(), key=lambda x: int(x[0])):  # Sort cards by number
                        f.write(f"{card}: {count}\n")
                break

        # Stops cameras and closes display window
        cam.release()
        cv2.destroyAllWindows()
    
    def generateCardSetHashes(self):
        setSize = 25  # Number of cards in set (for future expansion)
        for i in range(1, setSize +1):
            filename = 'CardsImages/' + str(i).rjust(3, '0') + '.jpg'
            cardhash = CardSet.CardSet.getHashes(imageName=filename,type='hash')
            cardhashmir = CardSet.CardSet.getHashes(imageName=filename,type='hashmir')
            cardhashud = CardSet.CardSet.getHashes(imageName=filename,type='hashud')
            cardhashudmir = CardSet.CardSet.getHashes(imageName=filename,type='hashudmir')
        
            #print("Card " + str(i) + " hashes generated.")  # For testing: print when each card's hashes are generated
            self.cardsearchhashs.update({str(i).rjust(3, '0'): {
                    'hash': cardhash,
                    'mir': cardhashmir,
                    'hud': cardhashud,
                    'hubmir': cardhashudmir
                }})

if __name__ == '__main__':
    # Start reading cards
    PokemonCardScanner() # Finds and reads live feed
