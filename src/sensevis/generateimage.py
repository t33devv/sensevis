from ._upscaler import generate_image_from_centroids

class ImageGenerator:
    def generate_image(self, centroids, userInput):
        generate_image_from_centroids(centroids, userInput)