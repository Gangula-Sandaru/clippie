import sys
import math
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QHBoxLayout, QFrame, QTextEdit, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPointF, QRect, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen, QFont, QLinearGradient, QBrush

from themes.theme_manager import theme_engine
from app_config import config
import random

class ResultOverlay(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: white;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 500;
                padding: 10px;
                selection-background-color: {acc};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {acc};
                border-radius: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

class OCRIndicator(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(180, 40)
        self.morph_phase = 0.0
        self.sparkles = []
        
        # Styles: Small, modern, fun glass-morphism
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        bg = "rgba(10, 10, 10, 240)"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 20px;
            }}
        """)
        
        # Adding a Luminous Halo (Drop Shadow Effect)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(acc))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 0, 12, 0)
        self.layout.setSpacing(8)
        
        # Text Label: Fun & Modern
        self.label = QLabel("Clippie Vision")
        self.label.setStyleSheet("color: white; font-family: 'Segoe UI Semibold'; font-size: 11px; letter-spacing: 0.5px; background: transparent; border: none;")
        
        # Globe container for custom paint
        self.globe_widget = QWidget()
        self.globe_widget.setFixedSize(24, 24)
        self.globe_widget.paintEvent = self.paint_globe
        
        self.layout.addWidget(self.globe_widget)
        self.layout.addWidget(self.label)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_all)
        self.anim_timer.start(30)

    def update_all(self):
        self.morph_phase += 0.08
        
        # Handle Sparkles
        if len(self.sparkles) < 5 and random.random() > 0.8:
            self.sparkles.append({
                'x': random.randint(0, 24),
                'y': random.randint(0, 24),
                'alpha': 255,
                'size': random.uniform(0.5, 1.5)
            })
            
        for s in self.sparkles[:]:
            s['alpha'] -= 10
            if s['alpha'] <= 0:
                self.sparkles.remove(s)
                
        self.globe_widget.update()

    def paint_globe(self, event):
        painter = QPainter(self.globe_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        cx, cy = 12, 12
        
        # Pulse Base Radius
        pulse = 1.0 + 0.15 * math.sin(self.morph_phase * 0.5)
        base_r = 7 * pulse
        
        path = QPainterPath()
        points = 8
        for i in range(points + 1):
            angle = (i / points) * 2 * math.pi
            # Organic deformation using multiple sine waves
            offset = 2.0 * math.sin(angle * 2 + self.morph_phase)
            offset += 1.0 * math.cos(angle * 3 - self.morph_phase * 0.7)
            
            r = base_r + offset
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            
            if i == 0: path.moveTo(px, py)
            else: path.lineTo(px, py)
        
        path.closeSubpath()
        
        # Glow & Gradient
        grad = QLinearGradient(0, 0, 24, 24)
        grad.setColorAt(0, QColor(acc))
        grad.setColorAt(1, QColor(acc).lighter(160))
        
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Center core light (Living Pulsing Core)
        # We can draw multiple layers for glow
        painter.setBrush(QColor(255, 255, 255, int(150 * pulse)))
        painter.drawEllipse(QPointF(cx-1.5, cy-1.5), 3, 3)
        
        # Draw Sparkles
        for s in self.sparkles:
            color = QColor(255, 255, 255, s['alpha'])
            painter.setBrush(color)
            painter.drawRect(QRectF(s['x'], s['y'], s['size'], s['size']))


class Toast(QLabel):
    def __init__(self, parent, text):
        super().__init__(text, parent)
        self.setFixedSize(160, 40)
        self.setAlignment(Qt.AlignCenter)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        bg = theme_engine.current_palette.get('main_bg', '#121212')
        self.setStyleSheet(f"background: {bg}; color: {acc}; border: 1px solid {acc}; border-radius: 20px; font-weight: 800;")
        
        self.move((parent.width() - self.width()) // 2, (parent.height() - self.height()) // 2 - 50)
        
        self.op = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.op)
        
        self.fade_anim = QPropertyAnimation(self.op, b"opacity")
        self.fade_anim.setDuration(1500)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.InExpo)
        self.fade_anim.finished.connect(self.deleteLater)
        self.fade_anim.start()
        self.show()

class MagicToolbar(QFrame):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.text = text
        self.setObjectName("MagicToolbar")
        self.setFixedSize(220, 36)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(5)
        
        # 1. Auto-Copy Checkbox/Toggle Button
        self.is_auto = config.settings.get("ocr_auto_copy", True)
        self.btn_auto = QPushButton("Auto-Copy: ON" if self.is_auto else "Auto-Copy: OFF")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setChecked(self.is_auto)
        self.btn_auto.setCursor(Qt.PointingHandCursor)
        self.btn_auto.clicked.connect(self.toggle_auto)
        
        # 2. Manual Copy Button
        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self.manual_copy)
        
        # 3. Retry Scan
        self.btn_retry = QPushButton("Retry")
        self.btn_retry.setCursor(Qt.PointingHandCursor)
        self.btn_retry.clicked.connect(parent.clear_selection)
        
        # 4. Close
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(parent.hide_results)
        
        layout.addWidget(self.btn_auto)
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.btn_retry)
        layout.addWidget(self.btn_close)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        bg = theme_engine.current_palette.get('card_bg', '#1e1e1e')
        text_color = theme_engine.current_palette.get('text_main', '#ffffff')
        
        self.setStyleSheet(f"""
            #MagicToolbar {{
                background: {bg};
                border: 1px solid {acc};
                border-radius: 12px;
            }}
            QPushButton {{
                background: transparent;
                color: {text_color};
                font-size: 11px;
                font-weight: bold;
                border: none;
                padding: 4px;
            }}
            QPushButton:hover {{ color: {acc}; }}
            QPushButton:checked {{ color: {acc}; }}
        """)

    def toggle_auto(self):
        self.is_auto = not self.is_auto
        config.save_setting("ocr_auto_copy", self.is_auto)
        self.btn_auto.setText("Auto-Copy: ON" if self.is_auto else "Auto-Copy: OFF")
        if self.is_auto:
            self.manual_copy()

    def manual_copy(self):
        import pyperclip
        pyperclip.copy(self.text)
        Toast(self.parent(), "Text Copied!")

class OCRWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setGeometry(QApplication.primaryScreen().geometry())
        
        self.progress = 0.0
        self.wave_phase = 0.0
        self.shimmer_progress = 0.0
        self.binary_particles = []
        self.original_pixmap = None
        self.blurred_pixmap = None
        self.final_rect = None
        self.final_text = ""
        self.show_results = False
        self.toolbar = None
        self.result_overlay = None
        self.indicator = None
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        
        self.shimmer_timer = QTimer(self)
        self.shimmer_timer.timeout.connect(self.update_shimmer)
        
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        self.base_color = QColor(acc)
        
        self.origin_x = 0
        self.origin_y = 0
        self._result_opacity = 0.0

        self.setFocusPolicy(Qt.StrongFocus)

    @pyqtProperty(float)
    def result_opacity(self): return self._result_opacity
    @result_opacity.setter
    def result_opacity(self, v):
        self._result_opacity = v
        self.update()

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
        self.shimmer_progress = 0.0
        self.final_rect = None
        self.final_text = ""
        self.show_results = False
        self._result_opacity = 0.0
        if self.toolbar:
            self.toolbar.hide()
            self.toolbar.deleteLater()
            self.toolbar = None
        if self.result_overlay:
            self.result_overlay.hide()
            self.result_overlay.deleteLater()
            self.result_overlay = None
            
        # Initialize Indicator in top-right
        if self.indicator:
            self.indicator.deleteLater()
        self.indicator = OCRIndicator(self)
        margin = 30
        self.indicator.move(self.width() - self.indicator.width() - margin, margin)
        
        # Fade-in for Indicator
        op = QGraphicsOpacityEffect(self.indicator)
        self.indicator.setGraphicsEffect(op)
        self.ind_fade = QPropertyAnimation(op, b"opacity")
        self.ind_fade.setDuration(500)
        self.ind_fade.setStartValue(0.0)
        self.ind_fade.setEndValue(1.0)
        self.ind_fade.start()
        self.indicator.show()

        self.anim_timer.start(16)
        self.setFocus()
        super().showEvent(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.hide()
        elif event.button() == Qt.LeftButton:
            self.clear_selection()
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if getattr(self, 'selection_start', None) is not None:
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and getattr(self, 'selection_start', None) is not None:
            self.selection_end = event.pos()
            rect = QRect(self.selection_start, self.selection_end).normalized()
            
            self.selection_start = None
            self.selection_end = None
            
            if rect.width() > 10 and rect.height() > 10:
                self.final_rect = rect
                if config.settings.get("magic_ocr_animation", True):
                    self.shimmer_progress = 0.0
                    self.shimmer_timer.start(16)
                    
                    # Capture with DPI Correction
                    ratio = QApplication.primaryScreen().devicePixelRatio()
                    phys_rect = QRect(
                        int(rect.x() * ratio), 
                        int(rect.y() * ratio), 
                        int(rect.width() * ratio), 
                        int(rect.height() * ratio)
                    )
                    
                    # Start OCR in background while shimmer plays
                    QTimer.singleShot(100, lambda pr=phys_rect, r=rect: self.perform_ocr_phys(pr, r))
                else:
                    ratio = QApplication.primaryScreen().devicePixelRatio()
                    phys_rect = QRect(int(rect.x()*ratio), int(rect.y()*ratio), int(rect.width()*ratio), int(rect.height()*ratio))
                    self.perform_ocr_phys(phys_rect, rect)
            else:
                self.update()

    def update_shimmer(self):
        self.shimmer_progress += 0.04 # Slower, more detailed animation
        
        # Generate binary particles for the cyberpunk effect
        if self.final_rect and self.shimmer_progress < 1.0:
            if len(self.binary_particles) < 30:
                self.binary_particles.append({
                    'x': random.randint(self.final_rect.left(), self.final_rect.right()),
                    'y': random.randint(self.final_rect.top(), self.final_rect.bottom()),
                    'char': random.choice(['0', '1']),
                    'life': random.uniform(0.1, 0.4)
                })
        
        if self.shimmer_progress >= 1.5:
            self.shimmer_progress = 0.0
            self.shimmer_timer.stop()
            self.binary_particles = []
        self.update()

    def clear_selection(self):
        self.show_results = False
        self.final_rect = None
        self.final_text = ""
        self._result_opacity = 0.0
        if self.toolbar:
            self.toolbar.hide()
            self.toolbar.deleteLater()
            self.toolbar = None
        if self.result_overlay:
            self.result_overlay.hide()
            self.result_overlay.deleteLater()
            self.result_overlay = None
        self.update()

    def hide_results(self):
        self.clear_selection()
        self.hide()

    def perform_ocr_phys(self, phys_rect, logical_rect):
        from ocr.capture import capture_screen_rect
        from ocr.processing import process_image
        try:
            # Capture the physical pixels
            img = capture_screen_rect(phys_rect.x(), phys_rect.y(), phys_rect.width(), phys_rect.height())
            text = process_image(img)
            
            if text:
                self.final_text = text
                self.show_results = True
                
                # Position toolbar based on logical coords
                tx = logical_rect.x() + (logical_rect.width() - 220) // 2
                ty = logical_rect.y() - 45 if logical_rect.y() > 50 else logical_rect.y() + logical_rect.height() + 10
                self.toolbar = MagicToolbar(self, text)
                self.toolbar.move(tx, ty)
                
                # Setup Result Overlay (Scrollable) at logical position
                self.result_overlay = ResultOverlay(self)
                self.result_overlay.setGeometry(logical_rect)
                self.result_overlay.setPlainText(text)
                
                # Check for Auto-copy toast
                if config.settings.get("ocr_auto_copy", True):
                    Toast(self, "Auto-Copied!")
                
                # Sync Opacity
                overlay_op = QGraphicsOpacityEffect(self.result_overlay)
                self.result_overlay.setGraphicsEffect(overlay_op)
                
                toolbar_op = QGraphicsOpacityEffect(self.toolbar)
                self.toolbar.setGraphicsEffect(toolbar_op)
                
                self.toolbar.show()
                self.result_overlay.show()

                # Unified Fade-in
                self.fade_anim = QPropertyAnimation(self, b"result_opacity")
                self.fade_anim.setDuration(400)
                self.fade_anim.setStartValue(0.0)
                self.fade_anim.setEndValue(1.0)
                
                self.tool_fade = QPropertyAnimation(toolbar_op, b"opacity")
                self.tool_fade.setDuration(400)
                self.tool_fade.setStartValue(0.0)
                self.tool_fade.setEndValue(1.0)
                
                self.over_fade = QPropertyAnimation(overlay_op, b"opacity")
                self.over_fade.setDuration(400)
                self.over_fade.setStartValue(0.0)
                self.over_fade.setEndValue(1.0)
                
                self.fade_anim.start()
                self.tool_fade.start()
                self.over_fade.start()
            else:
                self.hide()
                
        except Exception as e:
            print(f"OCR Error: {e}")
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

        if self.progress >= 0.8 and getattr(self, 'selection_start', None) is None:
            # Modern UI: Minimalist Instruction Subtext
            painter.setOpacity(max(0.0, (self.progress - 0.8) / 0.2))
            
            text_rect = self.rect()
            
            # Instruction Subtext (Modern, sleek, demi-bold)
            sub_font = QFont("Segoe UI", 10)
            sub_font.setWeight(QFont.DemiBold)
            sub_font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
            painter.setFont(sub_font)
            
            # Subtle shadow for clarity
            painter.setPen(QColor(0, 0, 0, 80))
            painter.drawText(text_rect.adjusted(1, 81, 1, 81), Qt.AlignCenter, "Drag to select area • Press ESC to exit")
            
            # Clean White Text
            painter.setPen(QColor(255, 255, 255, 160))
            painter.drawText(text_rect.adjusted(0, 80, 0, 80), Qt.AlignCenter, "Drag to select area • Press ESC to exit")
            
            painter.setOpacity(1.0)

        if getattr(self, 'selection_start', None) is not None:
            from PyQt5.QtCore import QRect
            rect = QRect(self.selection_start, self.selection_end).normalized()
            
            # Since the widget is translucent, clearing the overlay restores the raw desktop natively!
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(self.base_color), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

        # MAGIC SCAN SHIMMER & RESULT OVERLAY
        if self.final_rect:
            rect = self.final_rect
            
            # Clear background for the selected area
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw "Magic Scan" effect (Advanced Cyberpunk Mode)
            if self.shimmer_progress > 0 and self.shimmer_progress < 1.0:
                pos = self.shimmer_progress
                
                # 1. Binary Digital Rain
                painter.setPen(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 150))
                painter.setFont(QFont("Consolas", 10))
                for p in self.binary_particles:
                    painter.drawText(p['x'], p['y'], p['char'])

                # 2. Dual Laser Scan Lines
                painter.setPen(Qt.NoPen)
                
                # Main sharp line
                grad1 = QLinearGradient(0, rect.top(), 0, rect.bottom())
                grad1.setColorAt(max(0, pos-0.01), QColor(255, 255, 255, 0))
                grad1.setColorAt(pos, QColor(255, 255, 255, 255))
                grad1.setColorAt(min(1, pos+0.01), QColor(255, 255, 255, 0))
                painter.setBrush(grad1)
                painter.drawRect(rect.left(), int(rect.top() + rect.height()*pos)-1, rect.width(), 3)
                
                # Trailing wider glow
                grad2 = QLinearGradient(0, rect.top(), 0, rect.bottom())
                glow_pos = max(0, pos - 0.1)
                grad2.setColorAt(max(0, glow_pos-0.1), QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 0))
                grad2.setColorAt(glow_pos, QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100))
                grad2.setColorAt(min(1, glow_pos+0.1), QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 0))
                painter.setBrush(grad2)
                painter.drawRect(rect)

                # 3. "SCANNING..." HUD
                painter.setPen(QColor(255, 255, 255, 200))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.drawText(rect.left() + 5, rect.top() + 15, "ANALYZING BYTES...")

            # Draw Recognized Text Overlay Shell
            if self.show_results and self.final_text:
                painter.setOpacity(self._result_opacity)
                
                # Semi-transparent background for text area
                painter.setBrush(QColor(0, 0, 0, 160))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(rect, 4, 4)
                
                # Glowing border
                painter.setPen(QPen(self.base_color, 2))
                painter.drawRoundedRect(rect, 4, 4)
                
                painter.setOpacity(1.0)

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
