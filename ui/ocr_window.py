import sys
import math
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen

from themes.theme_manager import theme_engine

class OCRWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setGeometry(QApplication.primaryScreen().geometry())
        
        self.progress = 0.0
        self.wave_phase = 0.0
        self.original_pixmap = None
        self.blurred_pixmap = None
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        self.base_color = QColor(acc)
        
        self.origin_x = 0
        self.origin_y = 0

        self.setFocusPolicy(Qt.StrongFocus)

    def set_origin(self, x, y):
        self.origin_x = x
        self.origin_y = y

    def update_background(self):
        screen = QApplication.primaryScreen()
        # Grab the background behind the window to simulate blurring/water distortion
        self.original_pixmap = screen.grabWindow(0, self.x(), self.y(), self.width(), self.height())
        if not self.original_pixmap.isNull():
            scale_ratio = 12
            small = self.original_pixmap.scaled(
                max(1, self.width() // scale_ratio), 
                max(1, self.height() // scale_ratio), 
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )
            self.blurred_pixmap = small.scaled(
                self.width(), 
                self.height(), 
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )

    def showEvent(self, e):
        self.setGeometry(QApplication.primaryScreen().geometry())
        # We capture the screen to create the blurred liquid lens effect
        self.update_background()
        
        self.progress = 0.0
        self.wave_phase = 0.0
        self.anim_timer.start(16)
        self.setFocus()
        super().showEvent(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.hide()

    def update_animation(self):
        speed = 0.015 * (1.0 - self.progress) + 0.01
        self.progress += speed
        self.wave_phase += 0.15
        
        if self.progress >= 1.0:
            self.progress = 1.0
            self.anim_timer.stop()
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        corners = [
            (0, 0), (w, 0), (0, h), (w, h)
        ]
        max_dist = max(math.hypot(cx - self.origin_x, cy - self.origin_y) for cx, cy in corners)
        
        base_radius = self.progress * (max_dist + 50)
        
        if base_radius <= 0:
            return

        # Calculate how much to "normalize" the water effect back to clear reality
        # Starts fading out when progress passes 0.6, fully clear at 1.0
        normalize_fade = 1.0
        if self.progress > 0.6:
            normalize_fade = max(0.0, (1.0 - self.progress) / 0.4)

        if base_radius > 0:
            # Central mask for the "wet" OCR screen area bounds by the leading water ripple
            path = QPainterPath()
            path.addEllipse(QPointF(self.origin_x, self.origin_y), base_radius, base_radius)
            
            painter.save()
            painter.setClipPath(path)
            
            # 1: The permanent 80% opacity dark overlay (the OCR mask)
            # Fills inside the spreading water wave
            painter.setBrush(QColor(0, 0, 0, int(255 * 0.8)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
            
            # 2: The fading liquid refraction layer that makes the wave entrance magical
            if normalize_fade > 0:
                painter.setOpacity(normalize_fade)
                
                # Render the blurred underwater background
                if self.blurred_pixmap and not self.blurred_pixmap.isNull():
                    painter.save()
                    painter.translate(self.origin_x, self.origin_y)
                    # Gentle optical zoom mimicking water depth, settles back to 1.0
                    zoom = 1.0 + 0.02 * math.sin(self.progress * math.pi)
                    painter.scale(zoom, zoom)
                    painter.translate(-self.origin_x, -self.origin_y)
                    painter.drawPixmap(0, 0, self.blurred_pixmap)
                    painter.restore()
            
            painter.restore() # Release clip mask and opacity
        
        # Render 3D glass/water ripple rings (These fade naturally with distance)
        self.draw_ripple(painter, base_radius, max_dist, normalize_fade)
        self.draw_ripple(painter, base_radius * 0.85, max_dist, normalize_fade)
        self.draw_ripple(painter, base_radius * 0.70, max_dist, normalize_fade)

        if self.progress >= 1.0:
            # Add a dark drop shadow to the text so it's readable on any transparent background
            font = painter.font()
            font.setPointSize(28)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = self.rect()
            painter.setPen(QColor(0, 0, 0, 180)) # Shadow
            painter.drawText(text_rect.adjusted(2, 2, 2, 2), Qt.AlignCenter, "OCR Mode Active\nPress Esc or Right-click to exit")
            
            painter.setPen(QColor(255, 255, 255, 220)) # Text
            painter.drawText(text_rect, Qt.AlignCenter, "OCR Mode Active\nPress Esc or Right-click to exit")

    def draw_ripple(self, painter, radius, max_dist, global_fade):
        if radius <= 0: return
        
        # Ripples organically spread and dissolve as they move further away
        fade = max(0.0, 1.0 - (radius / (max_dist + 50)))
        fade *= global_fade # Ensure they completely vanish linearly as we normalize
        if fade <= 0: return
        
        # High-light crest of the water wave (refracting light towards viewer)
        alpha_crest = int(140 * fade)
        if alpha_crest > 0:
            pen = QPen(QColor(255, 255, 255, alpha_crest), max(1, int(3 * fade)))
            painter.setPen(pen)
            painter.drawEllipse(QPointF(self.origin_x, self.origin_y), radius, radius)
            
        # Shadow internal ridge of the wave trough (refracting away)
        alpha_trough = int(90 * fade)
        if alpha_trough > 0:
            pen = QPen(QColor(0, 0, 0, alpha_trough), max(1, int(4 * fade)))
            painter.setPen(pen)
            r_trough = radius - max(1, int(2 * fade))
            if r_trough > 0:
                painter.drawEllipse(QPointF(self.origin_x, self.origin_y), r_trough, r_trough)
