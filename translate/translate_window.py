import sys
import math
import random
import pyperclip
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QFrame, QTextEdit, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QComboBox
from PyQt5.QtCore import Qt, QTimer, QPointF, QRect, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen, QFont, QLinearGradient, QBrush

from themes.theme_manager import theme_engine
from app_config import config
from ui.ocr_window import ResultOverlay, MagicToolbar, OCRIndicator, Toast

class TranslateWorker(QThread):
    result = pyqtSignal(str, list, str, int)
    
    def __init__(self, img, target_lang, thread_id):
        super().__init__()
        self.img = img
        self.target_lang = target_lang
        self.thread_id = thread_id
        
    def run(self):
        try:
            from translate.translate_processing import process_translate_detailed
            text, words = process_translate_detailed(self.img, target_lang=self.target_lang, auto_copy=False)
            self.result.emit(text if text else "", words if words else [], "", self.thread_id)
        except Exception as e:
            self.result.emit("", [], str(e), self.thread_id)

class TranslateOverlay(ResultOverlay):
    def __init__(self, parent, words, ratio, target_lang):
        super().__init__(parent, words, ratio)
        for lbl, w in zip(self.labels, words):
            t_word = w.get('translated', w['text'])
            lbl.setText(t_word)
            lbl.setToolTip(f"Original: {w['text']}")
            lbl.setProperty("original_text", w['text'])
            # Give it a slightly different transparent background to feel like a translation
            acc = theme_engine.current_palette.get('accent', '#2563eb')
            lbl.setStyleSheet(f"QLabel {{ background-color: rgba(30,30,30,220); color: #facc15; font-family: 'Segoe UI'; font-size: {lbl.font().pointSize()}px; border-radius: 4px; border: 1px solid {acc}; selection-background-color: {acc}; }}")

    def update_language(self, target_lang):
        # Notify parent to re-translate entirely via background thread!
        if hasattr(self.parent(), 're_translate_current'):
            self.parent().re_translate_current()

class TranslationBox(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        acc = theme_engine.current_palette.get('accent', '#2563eb')
        bg = theme_engine.current_palette.get('card_bg', '#1e1e1e')
        
        self.setFixedWidth(300)
        self.setMinimumHeight(100)
        self.setObjectName("TranslationBox")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 15)
        
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(8)
        
        title_hl = QHBoxLayout()
        title_icon = QLabel("文") # Translation icon
        title_icon.setStyleSheet(f"color: {acc}; font-size: 16px; font-weight: bold;")
        title_label = QLabel("TRANSLATION")
        title_label.setStyleSheet(f"color: {acc}; font-family: 'Segoe UI Black'; font-size: 10px; letter-spacing: 1px;")
        title_hl.addWidget(title_icon)
        title_hl.addWidget(title_label)
        title_hl.addStretch()
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFrameStyle(QFrame.NoFrame)
        self.text_edit.setStyleSheet("background: transparent; color: white; font-size: 13px; font-family: 'Segoe UI';")
        
        inner_layout.addLayout(title_hl)
        inner_layout.addWidget(self.text_edit)
        layout.addLayout(inner_layout)
        
        self.setStyleSheet(f"#TranslationBox {{ background: {bg}; border: 2px solid {acc}; border-radius: 16px; }}")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        self.hide()

    def display_text(self, text):
        self.text_edit.setPlainText(text)
        self.show()
        # Adjust height based on content
        doc_height = self.text_edit.document().size().height()
        self.setFixedHeight(int(min(400, max(100, doc_height + 40))))

class TranslateWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.progress = 0.0
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
        self.translation_box = None
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

        self.lang_combo = QComboBox(self)
        
        self.lang_mapping = {
            "Auto Detect": "auto",
            "English": "en",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
            "Sinhala": "si"
        }
        for name, code in self.lang_mapping.items():
            self.lang_combo.addItem(name, code)
            
        self.lang_combo.setCurrentText("English")
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(30, 30, 30, 220);
                color: white;
                border: 1px solid {acc};
                border-radius: 6px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: #1e1e1e;
                color: white;
                selection-background-color: {acc};
                border: 1px solid {acc};
                border-radius: 4px;
            }}
        """)
        shadow_cmb = QGraphicsDropShadowEffect(self)
        shadow_cmb.setBlurRadius(15)
        shadow_cmb.setColor(QColor(0,0,0,150))
        shadow_cmb.setOffset(0, 4)
        self.lang_combo.setGraphicsEffect(shadow_cmb)
        self.lang_combo.hide()

    @property
    def current_lang_code(self):
        return self.lang_combo.currentData()

    @pyqtProperty(float)
    def result_opacity(self): return self._result_opacity
    @result_opacity.setter
    def result_opacity(self, v): self._result_opacity = v; self.update()

    def set_origin(self, x, y): self.origin_x, self.origin_y = x, y

    def on_language_changed(self, text):
        if self.show_results and self.result_overlay:
            target_lang = self.current_lang_code
            self.result_overlay.update_language(target_lang)
            # update bottom translation box
            from translate.translate_processing import translate_text
            new_text = translate_text(self.final_text, target_lang=target_lang, auto_copy=False)
            self.update_translation(new_text)

    def update_background(self):
        screen = QApplication.primaryScreen()
        self.original_pixmap = screen.grabWindow(0, self.x(), self.y(), self.width(), self.height())
        if not self.original_pixmap.isNull():
            small = self.original_pixmap.scaled(self.width()//12, self.height()//12, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.blurred_pixmap = small.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def showEvent(self, e):
        try:
            import win32gui
            win32gui.SetWindowDisplayAffinity(int(self.winId()), 0x00000011) # WDA_EXCLUDEFROMCAPTURE
        except Exception:
            pass

        self.setGeometry(QApplication.primaryScreen().geometry())
        self.update_background()
        self.progress = 0.0
        self.shimmer_progress = 0.0
        self.final_rect = None
        self.final_text = ""
        self.show_results = False
        self._result_opacity = 0.0
        if self.toolbar: self.toolbar.deleteLater(); self.toolbar = None
        if self.result_overlay: self.result_overlay.deleteLater(); self.result_overlay = None
        if self.indicator: self.indicator.deleteLater()
        if self.translation_box: self.translation_box.deleteLater(); self.translation_box = None
        
        self.indicator = OCRIndicator(self)
        self.indicator.label.setText("Clippie Translate")
        self.indicator.move(self.width() - self.indicator.width() - 30, 30)
        op = QGraphicsOpacityEffect(self.indicator)
        self.indicator.setGraphicsEffect(op)
        self.ind_fade = QPropertyAnimation(op, b"opacity")
        self.ind_fade.setDuration(500)
        self.ind_fade.setStartValue(0.0)
        self.ind_fade.setEndValue(1.0)
        self.ind_fade.start()
        self.indicator.show()
        
        self.lang_combo.move((self.width() - self.lang_combo.width()) // 2, 30)
        self.lang_combo.show()
        
        self.anim_timer.start(16)
        self.setFocus()
        super().showEvent(e)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton: self.hide()
        elif event.button() == Qt.LeftButton:
            self.clear_selection(); self.selection_start = event.pos(); self.selection_end = event.pos(); self.update()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'selection_start') and self.selection_start:
            self.selection_end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'selection_start') and self.selection_start:
            rect = QRect(self.selection_start, self.selection_end).normalized()
            self.selection_start = None
            self.selection_end = None
            if rect.width() > 10 and rect.height() > 10:
                self.final_rect = rect
                self.shimmer_progress = 0.0
                self.shimmer_timer.start(16)
                self.total_scroll_y = 0
                self.highest_finished_id = 0
                ratio = QApplication.primaryScreen().devicePixelRatio()
                phys = QRect(int(rect.x()*ratio), int(rect.y()*ratio), int(rect.width()*ratio), int(rect.height()*ratio))
                QTimer.singleShot(100, lambda p=phys, r=rect: self.perform_translate_phys(p, r))
            else:
                self.update()

    def update_shimmer(self):
        self.shimmer_progress += 0.04
        if self.final_rect and self.shimmer_progress < 1.0:
            if len(self.binary_particles) < 30:
                self.binary_particles.append({
                    'x': random.randint(self.final_rect.left(), self.final_rect.right()), 
                    'y': random.randint(self.final_rect.top(), self.final_rect.bottom()), 
                    'char': random.choice(['あ', 'Ω', '文', 'A', '가', 'ल'])
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
        if self.toolbar: self.toolbar.hide(); self.toolbar.deleteLater(); self.toolbar = None
        if self.result_overlay: self.result_overlay.hide(); self.result_overlay.deleteLater(); self.result_overlay = None
        if self.translation_box: self.translation_box.hide(); self.translation_box.deleteLater(); self.translation_box = None
        self.update()

    def hide_results(self): self.clear_selection(); self.hide()

    def update_translation(self, text):
        if not self.translation_box:
            self.translation_box = TranslationBox(self)
        self.translation_box.display_text(text)
        # Position it near the selection but not covering it if possible
        if self.final_rect:
            bx, by = self.final_rect.right() + 20, self.final_rect.top()
            if bx + 300 > self.width(): bx = self.final_rect.left() - 320
            if by + self.translation_box.height() > self.height(): by = self.height() - self.translation_box.height() - 20
            self.translation_box.move(max(20, bx), max(20, by))

    def perform_translate_phys(self, phys_rect, logical_rect):
        self.is_processing_ocr = True
        from ocr.capture import capture_screen_rect
        try:
            img = capture_screen_rect(phys_rect.x(), phys_rect.y(), phys_rect.width(), phys_rect.height())
        except Exception as e:
            print("Capture error:", e)
            self.is_processing_ocr = False
            return

        target_lang = self.current_lang_code
        
        if not hasattr(self, 'ocr_counter'):
            self.ocr_counter = 0
            self.ocr_threads = []
            
        self.ocr_counter += 1
        current_id = self.ocr_counter
        
        # Cleanup finished threads to prevent memory leaks
        self.ocr_threads = [t for t in self.ocr_threads if t.isRunning()]
        
        thread = TranslateWorker(img, target_lang, current_id)
        self.ocr_threads.append(thread)
        
        thread.result.connect(lambda text, words, err, t_id: self._on_ocr_finished(text, words, err, logical_rect, target_lang, t_id))
        thread.start()

    def _on_ocr_finished(self, text, words, err, logical_rect, target_lang, thread_id):
        self.is_processing_ocr = False
        if thread_id < getattr(self, 'highest_finished_id', 0):
            return
        self.highest_finished_id = thread_id
            
        if err:
            print("Translate Error:", err)
            self.shimmer_progress = 0.0
            self.shimmer_timer.stop()
            return
            
        old_overlay = self.result_overlay
        old_toolbar = self.toolbar
        
        self.shimmer_progress = 0.0
        self.shimmer_timer.stop()
        
        if text:
            self.final_text = text
            self.show_results = True
            self.toolbar = MagicToolbar(self, text)
            self.toolbar.move(logical_rect.x() + (logical_rect.width()-220)//2, logical_rect.y()-45 if logical_rect.y()>50 else logical_rect.y()+logical_rect.height()+10)
            ratio = QApplication.primaryScreen().devicePixelRatio()
            self.result_overlay = TranslateOverlay(self, words, ratio, target_lang)
            self.result_overlay.setGeometry(logical_rect)
            
            self.update_translation(text)
            
            self.toolbar.show()
            self.result_overlay.show()
            
            if old_overlay and old_overlay != self.result_overlay:
                old_overlay.hide()
                old_overlay.deleteLater()
            if old_toolbar and old_toolbar != self.toolbar:
                old_toolbar.hide()
                old_toolbar.deleteLater()
            
            if self._result_opacity < 1.0:
                self.fade_anim = QPropertyAnimation(self, b"result_opacity")
                self.fade_anim.setDuration(400)
                self.fade_anim.setStartValue(self._result_opacity)
                self.fade_anim.setEndValue(1.0)
                self.fade_anim.start()
        else: 
            if old_overlay:
                old_overlay.hide()
                old_overlay.deleteLater()
                self.result_overlay = None
            if old_toolbar:
                old_toolbar.hide()
                old_toolbar.deleteLater()
                self.toolbar = None
            # Do NOT hide the entire window, just clear the results and wait for text to scroll back in

    def update_animation(self):
        self.progress += 0.015 * (1.0 - self.progress) + 0.01
        if self.progress >= 1.0:
            self.progress = 1.0
            self.anim_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        max_dist = max(math.hypot(cx - self.origin_x, cy - self.origin_y) for cx, cy in [(0,0),(w,0),(0,h),(w,h)])
        base_radius = self.progress * (max_dist + 50)
        if base_radius <= 0: return
        norm_fade = 1.0 if self.progress <= 0.6 else max(0.0, (1.0 - self.progress) / 0.4)
        path = QPainterPath()
        path.addEllipse(QPointF(self.origin_x, self.origin_y), base_radius, base_radius)
        painter.save()
        painter.setClipPath(path)
        painter.setBrush(QColor(0,0,0,204))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        if norm_fade > 0 and self.blurred_pixmap:
            painter.setOpacity(norm_fade)
            painter.drawPixmap(0,0,self.blurred_pixmap)
        painter.restore()
        self.draw_ripple(painter, base_radius, max_dist, norm_fade)
        if self.progress >= 0.8 and not (hasattr(self, 'selection_start') and self.selection_start):
            painter.setOpacity(max(0.0, (self.progress - 0.8) / 0.2))
            painter.setPen(QColor(255,255,255,160))
            painter.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            painter.drawText(self.rect().adjusted(0,80,0,80), Qt.AlignCenter, "Scan area to translate • ESC to exit")
        if hasattr(self, 'selection_start') and self.selection_start:
            rect = QRect(self.selection_start, self.selection_end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#facc15"), 2, Qt.DashLine))
            painter.drawRect(rect)
        if self.final_rect:
            rect = self.final_rect
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            if 0 < self.shimmer_progress < 1.0:
                pos = self.shimmer_progress
                painter.setPen(QColor(250, 204, 21, 150))
                painter.setFont(QFont("Arial Unicode MS", 10))
                for p in self.binary_particles: painter.drawText(p['x'], p['y'], p['char'])
                grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
                grad.setColorAt(pos, QColor(255,255,255,255))
                painter.setBrush(grad)
                painter.drawRect(rect.left(), int(rect.top() + rect.height()*pos)-1, rect.width(), 3)
            if self.show_results:
                painter.setOpacity(self._result_opacity)
                painter.setBrush(QColor(0,0,0,160))
                painter.setPen(QPen(QColor("#facc15"),2))
                painter.drawRoundedRect(rect, 4, 4)

    def draw_ripple(self, painter, radius, max_dist, fade_in):
        fade = max(0.0, 1.0 - (radius / (max_dist + 50))) * fade_in
        if fade > 0:
            painter.setPen(QPen(QColor(255,255,255,int(140*fade)), max(1,int(3*fade))))
            painter.drawEllipse(QPointF(self.origin_x, self.origin_y), radius, radius)

    def wheelEvent(self, event):
        """Creates an 'Adaptive Mouse Bridge' exactly like OCR Window's, creating a fixed translation LENS."""
        try:
            import win32gui, win32api, win32con
            
            # Hide the old translation completely so the user has a clean view while scrolling the document below
            if self.result_overlay:
                self.result_overlay.hide()
                self.result_overlay.deleteLater()
                self.result_overlay = None

            hwnd_self = int(self.winId())
            exstyle = win32gui.GetWindowLong(hwnd_self, win32con.GWL_EXSTYLE)
            
            # 1. Open the bridge: Make our window hardware-transparent to the cursor
            win32gui.SetWindowLong(hwnd_self, win32con.GWL_EXSTYLE, exstyle | win32con.WS_EX_TRANSPARENT)
            
            # 2. Re-inject the very first scroll tick that we 'ate'
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
                        # Triggers new OCR translation explicitly at the resting state!
                        self.re_translate_current()
                    except Exception as e: print(f"Close bridge error: {e}")
                
                self.scroll_bridge_timer.timeout.connect(close_bridge)

            # Reset the timer. While the bridge is open, physical wheel events go straight to the app below!
            self.scroll_bridge_timer.start(150)
            
        except Exception as e: print(f"Scroll bridge error: {e}")
        event.accept()

    def re_translate_current(self):
        if not self.final_rect:
            return
            
        self.update_background()
        
        ratio = QApplication.primaryScreen().devicePixelRatio()
        phys = QRect(int(self.final_rect.x()*ratio), int(self.final_rect.y()*ratio), 
                     int(self.final_rect.width()*ratio), int(self.final_rect.height()*ratio))
                     
        self.perform_translate_phys(phys, self.final_rect)
