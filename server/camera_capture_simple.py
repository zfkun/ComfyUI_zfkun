import cv2
import os
import time

class CameraCaptureSimpleServer:

    def __init__(self, capture_source=0, save_dir='./', filename='0.jpg', capture_interval=30, bgr_color=(0, 0, 255), alpha=0.3, font_scale=0.6):
        self.source = capture_source
        self.save_dir = os.path.expanduser(save_dir)
        self.filename = filename
        self.capture_interval = capture_interval
        self.font_scale = font_scale
        self.color = bgr_color
        self.alpha = alpha

        self.filename_with_wildcard = '*' in filename
        self.cap = cv2.VideoCapture(capture_source)

        self.drawing = False
        self.ix, self.iy, self.ex, self.ey = -1, -1, -1, -1
        self.width = 0
        self.height = 0

        if not self.cap.isOpened():
            print("Unable to open camera")
            exit()

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.window_name = f'Exit: "Q" | Source: {self.source}, Speed: {self.capture_interval}, Output: "{os.path.join(self.save_dir, self.filename)}", Color: {self.color}, Alpha: {self.alpha}, FontScale: {self.font_scale}'

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.draw_rectangle)

    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.drawing:
                self.drawing = False
                self.ex, self.ey = x, y
                self.width = self.ex - self.ix
                self.height = self.ey - self.iy
            else:
                self.drawing = True
                self.ix, self.iy, self.ex, self.ey = x, y, x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.ex, self.ey = x, y
                self.width = self.ex - self.ix
                self.height = self.ey - self.iy

    def display_rectangle_info(self, frame):
        rect_xy = (self.ix, self.iy) if self.ix < self.ex and self.iy < self.ey else (self.ex, self.ey)
        text = f'Crop Range: {self.ix}, {self.iy}, {self.width}, {self.height}'
        # 确保文字在选区内
        # text_x = max(self.ix, self.ix + 10)
        # text_y = min(self.ey, self.ey - 10)
        xy = (30, 30)
        cv2.putText(frame, text, xy, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, self.color, 2)

    def start(self):
        counter = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Unable to get frame")
                break

            frame_copy = frame.copy()

            if self.drawing:
                # 选区边框
                cv2.rectangle(frame_copy, (self.ix, self.iy), (self.ex, self.ey), self.color, 1)

                # 选区填色
                overlay = frame_copy.copy()
                cv2.rectangle(overlay, (self.ix, self.iy), (self.ex, self.ey), self.color, -1)
                cv2.addWeighted(overlay, self.alpha, frame_copy, 1 - self.alpha, 0, frame_copy)
            elif not self.drawing and self.ex > self.ix and self.ey > self.iy:
                # 选区边框
                cv2.rectangle(frame_copy, (self.ix, self.iy), (self.ex, self.ey), self.color, 2)

                # 选区填色
                overlay = frame_copy.copy()
                cv2.rectangle(overlay, (self.ix, self.iy), (self.ex, self.ey), self.color, -1)
                cv2.addWeighted(overlay, self.alpha, frame_copy, 1 - self.alpha, 0, frame_copy)

                # 保存输出
                if counter % self.capture_interval == 0:
                    file_name = self.filename
                    if self.filename_with_wildcard:
                        file_name = file_name.replace('*', time.strftime('%Y%m%d_%H%M%S'))
                    save_path = os.path.join(self.save_dir, file_name)
                    if self.ex > self.ix and self.ey > self.iy:
                        frame = frame[self.iy:self.ey, self.ix:self.ex]
                    cv2.imwrite(save_path, frame)

            if self.width > 0 and self.height > 0:
                self.display_rectangle_info(frame_copy)

            cv2.imshow(self.window_name, frame_copy)
            counter += 1

            if cv2.waitKey(1) == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


__version__ = '0.0.1'

if __name__ == '__main__':
    
    import argparse

    def valid_range_float(x):
        x = float(x)
        if x < 0.0 or x > 1.0:
            raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
        return x
    
    def valid_bgr(bgr):
        bgr = int(bgr)
        if bgr < 0 or bgr > 255:
            raise argparse.ArgumentTypeError("BGR values should be between 0 and 255")
        return bgr
    
    def valid_source(source):
        if isinstance(source, int):
            source = int(source)
            if source < 0:
                raise argparse.ArgumentTypeError("source should be greater than 0")
            return source

        if isinstance(source, str):
            if not source.startswith('rtsp://'):
                raise argparse.ArgumentTypeError("source should start with 'rtsp://'")
            return source


    parser = argparse.ArgumentParser(description='a simple camera capture server')
    parser.add_argument('-s', type=valid_source, default=0, help='video capture source or rtsp url')
    parser.add_argument('-o', type=str, default='./', help='output dir for capture image')
    parser.add_argument('-f', type=str, default='0.jpg', help='output filename for capture image (suport "*" wildcard: "frame_*.jpg")')
    parser.add_argument('-t', type=int, default=30, help='capture interval by frame.')
    parser.add_argument('-c', type=valid_bgr, nargs=3, default=[0, 0, 255], help='BGR color for crop rectangle and text. BGR = (B, G, R)')
    parser.add_argument('-a', type=valid_range_float, default=0.3, help='color alpha for crop rectangle and text. 0 ~ 1')
    parser.add_argument('-fs', type=valid_range_float, default=0.6, help='font scale for text inside of crop rectangle.')

    args = parser.parse_args()

    camera = CameraCaptureSimpleServer(capture_source=args.s,
                                save_dir=args.o,
                                filename=args.f,
                                capture_interval=args.t,
                                bgr_color=tuple(args.c),
                                alpha=args.a,
                                font_scale=args.fs)
    camera.start()
