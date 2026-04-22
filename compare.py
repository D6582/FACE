import sys
import os
import cv2
import numpy as np

# Add project root to sys.path to allow imports
sys.path.append(os.getcwd())

try:
    from face_system.face_system.libs.utils.utils import compare_embedding
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Standard import failed, trying to adjust sys.path")
    # If the above import fails, try adding the specific path
    # Check if face_system exists in current directory
    if os.path.exists('face_system'):
         sys.path.append(os.path.join(os.getcwd(), 'face_system', 'face_system', 'libs'))
         from utils.utils import compare_embedding
         from sklearn.metrics.pairwise import cosine_similarity
    else:
        raise

image = cv2.imread('test.jpg')
image2 = cv2.imread('test2.jpg')

if image is None:
    print("Error: Could not read test.jpg")
    sys.exit(1)
if image2 is None:
    print("Error: Could not read test2.jpg")
    sys.exit(1)

print(f"Image 1 shape: {image.shape}")
print(f"Image 2 shape: {image2.shape}")

# Resize to ensure consistency (and reduce size)
image = cv2.resize(image, (112, 112))
image2 = cv2.resize(image2, (112, 112))

# Prepare embedding
# The function expects embedding to be reshaped to (1, -1) inside
# We flatten the image to simulate an embedding vector
embedding = image.flatten() 

# Prepare facebank
# The function implementation: facebank = np.array(facebank).squeeze(axis=1)
# This implies that the input facebank list elements should have a dimension of 1 at axis 1.
# So we reshape our flattened images to (1, -1)
facebank = [image.flatten().reshape(1, -1), image2.flatten().reshape(1, -1)]

print(f"Embedding shape: {embedding.shape}")
print(f"Facebank length: {len(facebank)}")
print(f"Facebank element shape: {facebank[0].shape}")

# Calculate and print similarities manually first
print("--- Detailed Similarity Check ---")
emb_reshaped = np.array(embedding).reshape(1, -1)
fb_reshaped = np.array(facebank).squeeze(axis=1)
similarities = cosine_similarity(emb_reshaped, fb_reshaped)[0]

for i, score in enumerate(similarities):
    print(f"Similarity with image {i+1}: {score:.6f}")

max_sim_idx = np.argmax(similarities)
print(f"Maximum similarity is {similarities[max_sim_idx]:.6f} at index {max_sim_idx}")
print("-------------------------------")

# Call the function
# We use image 1 as the query embedding, so it should match index 0 in the facebank
print("Comparing embedding (image 1) with facebank [image 1, image 2]...")
result_idx = compare_embedding(embedding, facebank)

print(f"Result index from function: {result_idx}")

if result_idx is not None:
    print(f"Match found at index: {result_idx}")
    if result_idx == 0:
        print("Success: Matches image 1 (itself)")
    elif result_idx == 1:
        print("Matches image 2")
else:
    print("No match found (similarity below threshold)")
