import cv2

class DRAW:
    colors = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'gray': (200, 200, 200),
    }

    def add_text_top_left(self, frame, text):
        if isinstance(text, str):
            text = text.split('\n')
        color = self.colors['blue']
        lineloc = 10
        lineheight = 30

        for line in text:
            lineloc += lineheight
            cv2.putText(frame, line, (10, lineloc), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)

    def add_text(self, frame, text, x, y, size=0.8, color='yellow', center=False):
        color = self.colors.get(color, (0, 255, 255))
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(text, font, size, 1)[0]

        if center:
            x -= textsize[0] // 2
        cv2.putText(frame, text, (int(x), int(y)), font, size, color, 1, cv2.LINE_AA)

    def crosshairs(self, frame, weight=1, color='green'):
        width = frame.shape[1]
        height = frame.shape[0]
        color = self.colors.get(color, (0, 255, 0))
        center_x = width // 2
        center_y = height // 2

        cv2.line(frame, (center_x, 0), (center_x, height), color, weight)
        cv2.line(frame, (0, center_y), (width, center_y), color, weight)
    
    def rect(self, frame, x1, y1, x2, y2, color='green', weight=1, filled=False):
        color = self.colors.get(color, (0, 255, 0))
        if filled:
            weight = -1
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, weight)
