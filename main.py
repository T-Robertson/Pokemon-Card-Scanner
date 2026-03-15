import cv2
import numpy as np
import utils
import time
import playsound
import json

class PokemonCardScanner:
    def __init__(self):
        # Initialize card data dictionary
        try:
            with open("Data.json", "r") as f:
                self.cardData = json.load(f)  # Load card data from Data.json file
        except FileNotFoundError:
            print("Data.json not found. Creating a new one.")
            self.cardData = utils.generateCardData()  # Generate card data dictionary if Data.json file doesn't exist
        print("Card data loaded.")
        # Generate card set hashes
        self.cardsearchhashs = utils.generateCardSetHashes()  # Generate hashes for card set and store in cardsearchhashs dictionary
        # Cards collected
        self.collectedCards = {}
        self.totalCardsCollected = 0
        
        #start main function
        self.main()
        
    def main(self):
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

            # An array of all 8 images
            imageArr = ([rot90frame, grayFrame, blurredFrame, edgedFrame],
                        [contourFrame, bigContour, imgWarpColored,  lastmatchingCard])

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
                    print(f"Matching card found: {self.cardData[str(matchingCard).rjust(3, '0')]['CardName']}")
                    lastmatchingCard = cv2.resize(cv2.imread('CardsImages/' + str(matchingCard).rjust(3, '0') + '.jpg'), (widthCard, heightCard))
                    #add function to ensure that the same card isn't counted multiple times in a row here
                    self.totalCardsCollected += 1  # Increment total cards collected
                    self.collectedCards.update({self.cardData[str(matchingCard).rjust(3, '0')]['CardName']: self.collectedCards.get(self.cardData[str(matchingCard).rjust(3, '0')]['CardName'], 0) + 1})  # Add matching card to collected cards
                    self.cardData[str(matchingCard).rjust(3, '0')]['CardName']
                    #add function to action matching card here
                    playsound.playsound(sound="Collect.wav")# Play sound when card is found
                    #wait to see what to do with matching card
                    time.sleep(3)  # Wait for 3 seconds before continuing to read cards
            if cv2.waitKey(1) & 0xFF == ord('q'):  # If reading from video, quit if 'q' is pressed
                print("Stopping card reader...")
                with open("Data.json", "w") as f:
                    json.dump(self.cardData, f, separators=(',', ': '), indent=4)  # Save card data to Data.json file
                
                with open("ScannedCards.txt", "w") as f:
                    f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")  # Save date and time of scan to ScannedCards.txt file
                    f.write("Total Cards Collected: " + str(self.totalCardsCollected) + "\n\n")
                    f.write("Cards Collected:\n")
                    for card, quantity in self.collectedCards.items():
                        f.write(str(card).rjust(3, '0') + ": " + str(quantity) + "\n")  # Save collected cards and quantities to ScannedCards.txt file
                break
        # Stops cameras and closes display window
        cam.release()
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    # Start reading cards
    PokemonCardScanner() # Finds and reads live feed
