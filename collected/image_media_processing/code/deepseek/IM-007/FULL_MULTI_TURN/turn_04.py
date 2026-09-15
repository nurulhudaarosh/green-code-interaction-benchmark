import cv2
import numpy as np


def compute_ahash(image_path, hash_size=8):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    resized = cv2.resize(img, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    avg = resized.mean()
    bits = (resized >= avg).flatten()
    hash_value = 0
    for bit in bits:
        hash_value = (hash_value << 1) | int(bit)
    return hash_value


def hamming_distance(hash_a, hash_b):
    return bin(hash_a ^ hash_b).count("1")


def find_similar_pairs(image_paths, threshold):
    hashes = [(path, compute_ahash(path)) for path in image_paths]
    similar_pairs = []
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            path_a, hash_a = hashes[i]
            path_b, hash_b = hashes[j]
            if hamming_distance(hash_a, hash_b) <= threshold:
                similar_pairs.append((path_a, path_b))
    return similar_pairs