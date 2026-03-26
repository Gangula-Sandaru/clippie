import sys
import math
import random
import pyperclip
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QHBoxLayout, QFrame, QTextEdit, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer, QPointF, QRect, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen, QFont, QLinearGradient, QBrush

from themes.theme_manager import theme_engine
from app_config import config

class ResultOverlay(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        self.setStyleSheet(f"QTextEdit {{ background-color: transparent; color: white; font-family: 'Segoe UI'; font-size: 14px; padding: 10px; selection-background-color: {acc}; }}")

class OCRIndicator(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(180, 40)
        self.morph_phase = 0.0
        self.sparkles = []
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        self.setStyleSheet(f"QFrame {{ background: rgba(10, 10, 10, 240); border: 1px solid rgba(255, 255, 255, 25); border-radius: 20px; }}")
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(20); shadow.setColor(QColor(acc)); shadow.setOffset(0, 0); self.setGraphicsEffect(shadow)
        self.layout = QHBoxLayout(self); self.layout.setContentsMargins(12, 0, 12, 0); self.layout.setSpacing(8)
        self.label = QLabel("Clippie Vision"); self.label.setStyleSheet("color: white; font-family: 'Segoe UI Semibold'; font-size: 11px; background: transparent;")
        self.globe_widget = QWidget(); self.globe_widget.setFixedSize(24, 24); self.globe_widget.paintEvent = self.paint_globe
        self.layout.addWidget(self.globe_widget); self.layout.addWidget(self.label)
        self.anim_timer = QTimer(self); self.anim_timer.timeout.connect(self.update_all); self.anim_timer.start(30)

    def update_all(self):
        self.morph_phase += 0.08
        if len(self.sparkles) < 5 and random.random() > 0.8:
            self.sparkles.append({'x': random.randint(0, 24), 'y': random.randint(0, 24), 'alpha': 255, 'size': random.uniform(0.5, 1.5)})
        for s in self.sparkles[:]:
            s['alpha'] -= 10
            if s['alpha'] <= 0: self.sparkles.remove(s)
        self.globe_widget.update()

    def paint_globe(self, event):
        painter = QPainter(self.globe_widget); painter.setRenderHint(QPainter.Antialiasing)
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        cx, cy = 12, 12; pulse = 1.0 + 0.15 * math.sin(self.morph_phase * 0.5); base_r = 7 * pulse
        path = QPainterPath(); points = 8
        for i in range(points + 1):
            angle = (i / points) * 2 * math.pi
            r = base_r + 2.0 * math.sin(angle * 2 + self.morph_phase) + 1.0 * math.cos(angle * 3 - self.morph_phase * 0.7)
            px, py = cx + r * math.cos(angle), cy + r * math.sin(angle)
            if i == 0: path.moveTo(px, py)
            else: path.lineTo(px, py)
        path.closeSubpath(); grad = QLinearGradient(0, 0, 24, 24); grad.setColorAt(0, QColor(acc)); grad.setColorAt(1, QColor(acc).lighter(160))
        painter.setBrush(grad); painter.setPen(Qt.NoPen); painter.drawPath(path)
        painter.setBrush(QColor(255, 255, 255, int(150 * pulse))); painter.drawEllipse(QPointF(cx-1.5, cy-1.5), 3, 3)
        
        for s in self.sparkles:
            color = QColor(255, 255, 255, s['alpha'])
            painter.setBrush(color); painter.setPen(Qt.NoPen)
            star_path = QPainterPath()
            sx, sy, size = s['x'], s['y'], s['size'] * 2.5
            
            # Draw a sleek 4-pointed star
            star_path.moveTo(sx, sy - size)
            star_path.quadTo(sx, sy, sx + size, sy)
            star_path.quadTo(sx, sy, sx, sy + size)
            star_path.quadTo(sx, sy, sx - size, sy)
            star_path.quadTo(sx, sy, sx, sy - size)
            
            painter.drawPath(star_path)

class Toast(QLabel):
    def __init__(self, parent, text):
        super().__init__(text, parent); self.setFixedSize(160, 40); self.setAlignment(Qt.AlignCenter)
        acc = theme_engine.current_palette.get('accent', '#2563eb'); bg = theme_engine.current_palette.get('main_bg', '#121212')
        self.setStyleSheet(f"background: {bg}; color: {acc}; border: 1px solid {acc}; border-radius: 20px; font-weight: 800;")
        self.move((parent.width() - self.width()) // 2, (parent.height() - self.height()) // 2 - 50)
        self.op = QGraphicsOpacityEffect(self); self.setGraphicsEffect(self.op)
        self.fade_anim = QPropertyAnimation(self.op, b"opacity"); self.fade_anim.setDuration(1500)
        self.fade_anim.setStartValue(1.0); self.fade_anim.setEndValue(0.0); self.fade_anim.finished.connect(self.deleteLater); self.fade_anim.start(); self.show()

class MagicToolbar(QFrame):
    def __init__(self, parent, text):
        super().__init__(parent); self.text = text; self.setObjectName("MagicToolbar"); self.setFixedSize(220, 36)
        layout = QHBoxLayout(self); layout.setContentsMargins(8, 0, 8, 0); layout.setSpacing(5)
        self.is_auto = config.settings.get("ocr_auto_copy", True)
        self.btn_auto = QPushButton("Auto-Copy: ON" if self.is_auto else "Auto-Copy: OFF"); self.btn_auto.setCheckable(True); self.btn_auto.setChecked(self.is_auto)
        self.btn_auto.clicked.connect(self.toggle_auto); self.btn_copy = QPushButton("Copy"); self.btn_copy.clicked.connect(self.manual_copy)
        self.btn_retry = QPushButton("Retry"); self.btn_retry.clicked.connect(parent.clear_selection)
        self.btn_close = QPushButton("✕"); self.btn_close.setFixedSize(24, 24); self.btn_close.clicked.connect(parent.hide_results)
        for b in [self.btn_auto, self.btn_copy, self.btn_retry, self.btn_close]:
            b.setCursor(Qt.PointingHandCursor); layout.addWidget(b)
        acc = theme_engine.current_palette.get('accent', '#2563eb'); bg = theme_engine.current_palette.get('card_bg', '#1e1e1e')
        text_color = theme_engine.current_palette.get('text_main', '#ffffff')
        self.setStyleSheet(f"#MagicToolbar {{ background: {bg}; border: 1px solid {acc}; border-radius: 12px; }} QPushButton {{ background: transparent; color: {text_color}; font-size: 11px; font-weight: bold; border: none; padding: 4px; }} QPushButton:hover, QPushButton:checked {{ color: {acc}; }}")

    def toggle_auto(self):
        self.is_auto = not self.is_auto; config.save_setting("ocr_auto_copy", self.is_auto)
        self.btn_auto.setText("Auto-Copy: ON" if self.is_auto else "Auto-Copy: OFF")
        if self.is_auto: self.manual_copy()

    def manual_copy(self): pyperclip.copy(self.text); Toast(self.parent(), "Text Copied!")

class OCRWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool); self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.progress = 0.0; self.shimmer_progress = 0.0; self.binary_particles = []; self.original_pixmap = None; self.blurred_pixmap = None
        self.final_rect = None; self.final_text = ""; self.show_results = False; self.toolbar = None; self.result_overlay = None; self.indicator = None
        self.anim_timer = QTimer(self); self.anim_timer.timeout.connect(self.update_animation)
        self.shimmer_timer = QTimer(self); self.shimmer_timer.timeout.connect(self.update_shimmer)
        acc = theme_engine.current_palette.get('accent', '#2563eb'); self.base_color = QColor(acc); self.origin_x = 0; self.origin_y = 0; self._result_opacity = 0.0; self.setFocusPolicy(Qt.StrongFocus)

    @pyqtProperty(float)
    def result_opacity(self): return self._result_opacity
    @result_opacity.setter
    def result_opacity(self, v): self._result_opacity = v; self.update()

    def set_origin(self, x, y): self.origin_x, self.origin_y = x, y

    def update_background(self):
        screen = QApplication.primaryScreen(); self.original_pixmap = screen.grabWindow(0, self.x(), self.y(), self.width(), self.height())
        if not self.original_pixmap.isNull():
            small = self.original_pixmap.scaled(self.width()//12, self.height()//12, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.blurred_pixmap = small.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def showEvent(self, e):
        self.setGeometry(QApplication.primaryScreen().geometry()); self.update_background()
        self.progress = 0.0; self.shimmer_progress = 0.0; self.final_rect = None; self.final_text = ""; self.show_results = False; self._result_opacity = 0.0
        if self.toolbar: self.toolbar.deleteLater(); self.toolbar = None
        if self.result_overlay: self.result_overlay.deleteLater(); self.result_overlay = None
        if self.indicator: self.indicator.deleteLater()
        
        # Restore the Clippie Vision Top-Right Indicator Animation
        self.indicator = OCRIndicator(self)
        self.indicator.move(self.width() - self.indicator.width() - 30, 30)
        op = QGraphicsOpacityEffect(self.indicator)
        self.indicator.setGraphicsEffect(op)
        self.ind_fade = QPropertyAnimation(op, b"opacity")
        self.ind_fade.setDuration(500)
        self.ind_fade.setStartValue(0.0)
        self.ind_fade.setEndValue(1.0)
        self.ind_fade.start()
        self.indicator.show()
        
        self.anim_timer.start(16); self.setFocus(); super().showEvent(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton: self.hide()
        elif event.button() == Qt.LeftButton:
            self.clear_selection(); self.selection_start = event.pos(); self.selection_end = event.pos(); self.update()

    def mouseMoveEvent(self, event):
        if getattr(self, 'selection_start', None): self.selection_end = event.pos(); self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and getattr(self, 'selection_start', None):
            rect = QRect(self.selection_start, self.selection_end).normalized(); self.selection_start = None; self.selection_end = None
            if rect.width() > 10 and rect.height() > 10:
                self.final_rect = rect; self.shimmer_progress = 0.0; self.shimmer_timer.start(16)
                ratio = QApplication.primaryScreen().devicePixelRatio()
                phys = QRect(int(rect.x()*ratio), int(rect.y()*ratio), int(rect.width()*ratio), int(rect.height()*ratio))
                QTimer.singleShot(100, lambda p=phys, r=rect: self.perform_ocr_phys(p, r))
            else: self.update()

    def update_shimmer(self):
        self.shimmer_progress += 0.04
        if self.final_rect and self.shimmer_progress < 1.0:
            if len(self.binary_particles) < 30: self.binary_particles.append({'x': random.randint(self.final_rect.left(), self.final_rect.right()), 'y': random.randint(self.final_rect.top(), self.final_rect.bottom()), 'char': random.choice(['0', '1'])})
        if self.shimmer_progress >= 1.5: self.shimmer_progress = 0.0; self.shimmer_timer.stop(); self.binary_particles = []
        self.update()

    def clear_selection(self):
        self.show_results = False; self.final_rect = None; self.final_text = ""; self._result_opacity = 0.0
        if self.toolbar: self.toolbar.hide(); self.toolbar.deleteLater(); self.toolbar = None
        if self.result_overlay: self.result_overlay.hide(); self.result_overlay.deleteLater(); self.result_overlay = None
        self.update()

    def hide_results(self): self.clear_selection(); self.hide()

    def perform_ocr_phys(self, phys_rect, logical_rect):
        from ocr.capture import capture_screen_rect; from ocr.processing import process_image
        try:
            img = capture_screen_rect(phys_rect.x(), phys_rect.y(), phys_rect.width(), phys_rect.height())
            text = process_image(img)
            if text:
                self.final_text = text; self.show_results = True
                self.toolbar = MagicToolbar(self, text); self.toolbar.move(logical_rect.x() + (logical_rect.width()-220)//2, logical_rect.y()-45 if logical_rect.y()>50 else logical_rect.y()+logical_rect.height()+10)
                self.result_overlay = ResultOverlay(self); self.result_overlay.setGeometry(logical_rect); self.result_overlay.setPlainText(text)
                if config.settings.get("ocr_auto_copy", True): Toast(self, "Auto-Copied!")
                self.toolbar.show(); self.result_overlay.show()
                self.fade_anim = QPropertyAnimation(self, b"result_opacity"); self.fade_anim.setDuration(400); self.fade_anim.setStartValue(0.0); self.fade_anim.setEndValue(1.0); self.fade_anim.start()
            else: self.hide()
        except: self.hide()

    def update_animation(self):
        self.progress += 0.015 * (1.0 - self.progress) + 0.01
        if self.progress >= 1.0: self.progress = 1.0; self.anim_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); max_dist = max(math.hypot(cx - self.origin_x, cy - self.origin_y) for cx, cy in [(0,0),(w,0),(0,h),(w,h)])
        base_radius = self.progress * (max_dist + 50)
        if base_radius <= 0: return
        norm_fade = 1.0 if self.progress <= 0.6 else max(0.0, (1.0 - self.progress) / 0.4)
        path = QPainterPath(); path.addEllipse(QPointF(self.origin_x, self.origin_y), base_radius, base_radius)
        painter.save(); painter.setClipPath(path); painter.setBrush(QColor(0,0,0,204)); painter.setPen(Qt.NoPen); painter.drawRect(self.rect())
        if norm_fade > 0 and self.blurred_pixmap: painter.setOpacity(norm_fade); painter.drawPixmap(0,0,self.blurred_pixmap)
        painter.restore()
        self.draw_ripple(painter, base_radius, max_dist, norm_fade)
        if self.progress >= 0.8 and not getattr(self, 'selection_start', None):
            painter.setOpacity(max(0.0, (self.progress - 0.8) / 0.2)); painter.setPen(QColor(255,255,255,160)); painter.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            painter.drawText(self.rect().adjusted(0,80,0,80), Qt.AlignCenter, "Drag to select area • Scroll to navigate • ESC to exit")
        if getattr(self, 'selection_start', None):
            rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear); painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver); painter.setPen(QPen(self.base_color, 2, Qt.DashLine)); painter.drawRect(rect)
        if self.final_rect:
            rect = self.final_rect; painter.setCompositionMode(QPainter.CompositionMode_Clear); painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            if 0 < self.shimmer_progress < 1.0:
                pos = self.shimmer_progress; painter.setPen(QColor(self.base_color.red(),self.base_color.green(),self.base_color.blue(),150)); painter.setFont(QFont("Consolas", 10))
                for p in self.binary_particles: painter.drawText(p['x'], p['y'], p['char'])
                grad = QLinearGradient(0, rect.top(), 0, rect.bottom()); grad.setColorAt(pos, QColor(255,255,255,255)); painter.setBrush(grad); painter.drawRect(rect.left(), int(rect.top() + rect.height()*pos)-1, rect.width(), 3)
            if self.show_results: painter.setOpacity(self._result_opacity); painter.setBrush(QColor(0,0,0,160)); painter.setPen(QPen(self.base_color,2)); painter.drawRoundedRect(rect, 4, 4)

    def draw_ripple(self, painter, radius, max_dist, fade_in):
        fade = max(0.0, 1.0 - (radius / (max_dist + 50))) * fade_in
        if fade > 0: painter.setPen(QPen(QColor(255,255,255,int(140*fade)), max(1,int(3*fade)))); painter.drawEllipse(QPointF(self.origin_x, self.origin_y), radius, radius)

    def wheelEvent(self, event):
        """Creates an 'Adaptive Mouse Bridge' that lets physical scroll events fall through natively."""
        try:
            import win32gui, win32api, win32con
            
            # Auto-clear the current scan box so the user has a clean view to scroll
            self.clear_selection()
            
            hwnd_self = int(self.winId())
            exstyle = win32gui.GetWindowLong(hwnd_self, win32con.GWL_EXSTYLE)
            
            # 1. Open the bridge: Make our window hardware-transparent to the cursor
            win32gui.SetWindowLong(hwnd_self, win32con.GWL_EXSTYLE, exstyle | win32con.WS_EX_TRANSPARENT)
            
            # 2. Re-inject the very first scroll tick that we 'ate', so the app below doesn't miss it
            delta = event.angleDelta().y()
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
            
            # 3. Keep the bridge open for continuous scrolling. Once the user stops for 150ms, close it.
            if not hasattr(self, 'scroll_bridge_timer'):
                self.scroll_bridge_timer = QTimer(self)
                self.scroll_bridge_timer.setSingleShot(True)
                def close_bridge():
                    try:
                        h = int(self.winId())
                        e = win32gui.GetWindowLong(h, win32con.GWL_EXSTYLE)
                        win32gui.SetWindowLong(h, win32con.GWL_EXSTYLE, e & ~win32con.WS_EX_TRANSPARENT)
                    except Exception as e:
                        print(f"Failed to close scroll bridge: {e}")
                
                self.scroll_bridge_timer.timeout.connect(close_bridge)

            # Reset the timer. While the bridge is open, physical wheel events go straight to the app below!
            self.scroll_bridge_timer.start(150)
            
        except Exception as e: 
            print(f"Scroll bridge error: {e}")
            
        event.accept()
