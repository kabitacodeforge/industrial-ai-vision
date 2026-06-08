import cv2

class Camera:
    def __init__(self, index=0):
        self.index = index
        self.cap = None

    def start(self):
        """Start camera safely"""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.index)
        return self.cap

    def read(self):
        """Read single frame"""
        if self.cap is None:
            self.start()

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    def stop(self):
        """Release camera properly"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        cv2.destroyAllWindows()


# Global instance (used by API)
camera = Camera()


# ---------------- HELPER FUNCTIONS ----------------

def get_frame():
    """Get single frame safely"""
    return camera.read()


def start_camera():
    """Initialize camera"""
    camera.start()


def stop_camera():
    """Release camera safely"""
    camera.stop()