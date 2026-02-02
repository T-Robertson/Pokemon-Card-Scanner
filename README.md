Pokémon Card Scanner lite
=========================
Fork of https://github.com/NolanAmblard/Pokemon-Card-Scanner/tree/main

This repository contains Python code for a Pokémon card scanner and identifier for any card with an image listed in the folder

The computer's webcam is used to read the card.

Using the `OpenCV` library, we can get a normalized scan (think PDF scanner apps) of the Pokémon card in the feed by doing the following:
 1. Taking in a single image or video feed
 2. Finding edges in the image/frame
 3. Finding the biggest contour that is a rectangle
 4. Finding the corners of the biggest contour
 5. Identifying which corner is which (i.e. reordering the corners to ensure that they are in the order: topLeft, topRight, bottomLeft, bottomRight)
 6. Creating a transformation matrix based on the original corners to transform the image / frame of the card into a vertical rectangle   
 
It then gets the hashes (average hash, whash, phash, dhash) of the scanned card using the `ImageHash` library and compares these hashes to their counterparts for each card in the set by finding the distance between these hashes. By using four different hashing methods, we can reduce the margin of error that only using one may introduce.  A smaller distance is indicative of more cards being more similar. A cutoff value is defined so as if a hash distance is smaller than it, we can assume the images are similar. 

These hashes generated everytime the program starts, and are stored in a library as a refence when cards are identifed. 

If a similar card is found, information on said card is printed to the console. If the code was using a live feed, it is aborted.
