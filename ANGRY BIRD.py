import sys
import math
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QComboBox, 
                              QSlider, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import (Qt, QTimer, QPointF, QRectF, pyqtSignal, QPropertyAnimation,
                           QEasingCurve, QSize)
from PyQt6.QtGui import (QPainter, QColor, QBrush, QPen, QFont, QRadialGradient,
                          QLinearGradient, QPainterPath, QPixmap, QTransform,
                          QFontMetrics)


TRANSLATIONS = {
    'en': {
        'title': 'ANGRY BIRD',
        'score': 'Score',
        'level': 'Level',
        'birds_left': 'Birds Left',
        'new_game': 'New Game',
        'next_level': 'Next Level',
        'theme': 'Theme',
        'language': 'Language',
        'light': 'Light',
        'dark': 'Dark',
        'game_over': 'GAME OVER',
        'level_complete': 'LEVEL COMPLETE!',
        'drag_to_aim': 'Drag bird to aim & release to shoot',
        'pigs_left': 'Pigs Left',
        'power': 'Power',
        'angle': 'Angle',
        'restart': 'Restart',
        'victory': 'VICTORY!',
        'total_score': 'Total Score',
    },
    'fa': {
        'title': 'پرنده خشمگین',
        'score': 'امتیاز',
        'level': 'مرحله',
        'birds_left': 'پرنده‌های باقی',
        'new_game': 'بازی جدید',
        'next_level': 'مرحله بعد',
        'theme': 'تم',
        'language': 'زبان',
        'light': 'روشن',
        'dark': 'تاریک',
        'game_over': 'بازی تمام شد',
        'level_complete': 'مرحله کامل شد!',
        'drag_to_aim': 'پرنده را بکشید و رها کنید',
        'pigs_left': 'خوک‌های باقی',
        'power': 'قدرت',
        'angle': 'زاویه',
        'restart': 'شروع مجدد',
        'victory': 'پیروزی!',
        'total_score': 'امتیاز کل',
    },
    'zh': {
        'title': '愤怒的小鸟',
        'score': '分数',
        'level': '关卡',
        'birds_left': '剩余小鸟',
        'new_game': '新游戏',
        'next_level': '下一关',
        'theme': '主题',
        'language': '语言',
        'light': '浅色',
        'dark': '深色',
        'game_over': '游戏结束',
        'level_complete': '关卡完成！',
        'drag_to_aim': '拖动小鸟瞄准并释放射击',
        'pigs_left': '剩余猪',
        'power': '力量',
        'angle': '角度',
        'restart': '重新开始',
        'victory': '胜利！',
        'total_score': '总分',
    }
}


class Bird:
    def __init__(self, x, y, bird_type='red'):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 18
        self.bird_type = bird_type
        self.launched = False
        self.alive = True
        self.trail = []
        self.rotation = 0
        self.special_used = False
        self.bounce_count = 0
        self.max_bounces = 2
        
    def launch(self, vx, vy):
        self.vx = vx
        self.vy = vy
        self.launched = True
        
    def update(self, gravity=0.4):
        if self.launched and self.alive:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 25:
                self.trail.pop(0)
            self.vy += gravity
            self.x += self.vx
            self.y += self.vy
            self.rotation += self.vx * 2
            
    def get_rect(self):
        return QRectF(self.x - self.radius, self.y - self.radius,
                     self.radius * 2, self.radius * 2)


class Pig:
    def __init__(self, x, y, size='medium'):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        if size == 'small':
            self.radius = 14
            self.health = 1
            self.max_health = 1
        elif size == 'large':
            self.radius = 26
            self.health = 3
            self.max_health = 3
        else:
            self.radius = 20
            self.health = 2
            self.max_health = 2
        self.alive = True
        self.damage_flash = 0
        self.wobble = 0
        self.wobble_dir = 1
        
    def take_damage(self, damage=1):
        self.health -= damage
        self.damage_flash = 10
        self.wobble = 8
        if self.health <= 0:
            self.alive = False
            return True
        return False
        
    def update(self):
        if self.damage_flash > 0:
            self.damage_flash -= 1
        if self.wobble > 0:
            self.wobble -= 0.5
            
    def get_rect(self):
        return QRectF(self.x - self.radius, self.y - self.radius,
                     self.radius * 2, self.radius * 2)


class Block:
    def __init__(self, x, y, w, h, material='wood'):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.material = material
        if material == 'wood':
            self.health = 3
            self.max_health = 3
        elif material == 'stone':
            self.health = 6
            self.max_health = 6
        elif material == 'glass':
            self.health = 1
            self.max_health = 1
        elif material == 'ice':
            self.health = 2
            self.max_health = 2
        self.alive = True
        self.damage_flash = 0
        self.crack_level = 0
        
    def take_damage(self, damage=1):
        self.health -= damage
        self.damage_flash = 8
        self.crack_level = int((1 - self.health / self.max_health) * 3)
        if self.health <= 0:
            self.alive = False
            return True
        return False
        
    def update(self):
        if self.damage_flash > 0:
            self.damage_flash -= 1
            
    def get_rect(self):
        return QRectF(self.x, self.y, self.w, self.h)


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-4, 4)
        self.vy = vy if vy is not None else random.uniform(-6, -1)
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.size = random.uniform(3, 8)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
        return self.life > 0


class GameCanvas(QWidget):
    score_changed = pyqtSignal(int)
    game_over_signal = pyqtSignal(bool)
    birds_changed = pyqtSignal(int)
    pigs_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        
        self.theme = 'light'
        self.score = 0
        self.level = 1
        self.game_state = 'playing'
        
        self.birds = []
        self.pigs = []
        self.blocks = []
        self.particles = []
        self.current_bird_index = 0
        self.bird_queue = []
        
        self.slingshot_x = 120
        self.slingshot_y_base = 0
        self.slingshot_anchor = QPointF(0, 0)
        
        self.dragging = False
        self.drag_pos = QPointF(0, 0)
        self.max_drag = 80
        
        self.active_bird = None
        self.bird_in_flight = False
        
        self.ground_y = 0
        self.camera_x = 0
        self.target_camera_x = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)
        
        self.anim_timer = 0
        self.stars = [(random.randint(0, 2000), random.randint(0, 200), 
                      random.uniform(0.5, 2)) for _ in range(50)]
        
        self.setup_level(1)
        
    def setup_level(self, level):
        self.birds = []
        self.pigs = []
        self.blocks = []
        self.particles = []
        self.current_bird_index = 0
        self.bird_in_flight = False
        self.camera_x = 0
        self.target_camera_x = 0
        self.game_state = 'playing'
        
        bird_types = ['red', 'blue', 'yellow', 'black', 'white']
        
        if level == 1:
            self.bird_queue = ['red', 'red', 'red', 'blue']
            self.pigs = [
                Pig(500, 0, 'medium'),
                Pig(600, 0, 'small'),
            ]
            self.blocks = [
                Block(460, 0, 20, 80, 'wood'),
                Block(620, 0, 20, 80, 'wood'),
                Block(460, 0, 180, 20, 'wood'),
            ]
        elif level == 2:
            self.bird_queue = ['red', 'blue', 'yellow', 'red', 'black']
            self.pigs = [
                Pig(500, 0, 'medium'),
                Pig(650, 0, 'large'),
                Pig(750, 0, 'small'),
            ]
            self.blocks = [
                Block(460, 0, 20, 100, 'stone'),
                Block(700, 0, 20, 100, 'stone'),
                Block(460, 0, 260, 20, 'stone'),
                Block(550, 0, 20, 60, 'wood'),
                Block(620, 0, 20, 60, 'wood'),
                Block(550, 0, 90, 20, 'glass'),
            ]
        elif level == 3:
            self.bird_queue = ['yellow', 'black', 'white', 'blue', 'red', 'yellow']
            self.pigs = [
                Pig(480, 0, 'small'),
                Pig(580, 0, 'medium'),
                Pig(700, 0, 'large'),
                Pig(820, 0, 'small'),
                Pig(900, 0, 'medium'),
            ]
            self.blocks = [
                Block(440, 0, 20, 120, 'stone'),
                Block(740, 0, 20, 120, 'stone'),
                Block(440, 0, 320, 20, 'stone'),
                Block(500, 0, 20, 80, 'wood'),
                Block(660, 0, 20, 80, 'wood'),
                Block(500, 0, 180, 20, 'wood'),
                Block(560, 0, 20, 40, 'glass'),
                Block(620, 0, 20, 40, 'glass'),
                Block(560, 0, 80, 20, 'glass'),
                Block(800, 0, 20, 80, 'ice'),
                Block(920, 0, 20, 80, 'ice'),
                Block(800, 0, 140, 20, 'ice'),
            ]
        else:
            num_birds = min(3 + level, 8)
            num_pigs = min(2 + level, 7)
            self.bird_queue = [random.choice(bird_types) for _ in range(num_birds)]
            
            base_x = 450
            for i in range(num_pigs):
                size = random.choice(['small', 'medium', 'large'])
                self.pigs.append(Pig(base_x + i * 120, 0, size))
            
            materials = ['wood', 'stone', 'glass', 'ice']
            for i in range(num_pigs):
                mat = random.choice(materials)
                bx = base_x + i * 120 - 30
                self.blocks.append(Block(bx, 0, 20, 80, mat))
                self.blocks.append(Block(bx + 60, 0, 20, 80, mat))
                self.blocks.append(Block(bx, 0, 80, 20, mat))
        
        self._fix_positions()
        self._place_next_bird()
        
    def _fix_positions(self):
        h = self.height() if self.height() > 0 else 500
        self.ground_y = h - 80
        self.slingshot_y_base = self.ground_y
        self.slingshot_anchor = QPointF(self.slingshot_x, self.ground_y - 90)
        
        for pig in self.pigs:
            pig.y = self.ground_y - pig.radius
            
        for block in self.blocks:
            if block.y == 0:
                block.y = self.ground_y - block.h
                
    def _place_next_bird(self):
        if self.current_bird_index < len(self.bird_queue):
            btype = self.bird_queue[self.current_bird_index]
            bird = Bird(self.slingshot_anchor.x(), self.slingshot_anchor.y(), btype)
            self.active_bird = bird
            self.bird_in_flight = False
        else:
            self.active_bird = None
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fix_positions()
        if self.active_bird and not self.bird_in_flight:
            self.active_bird.x = self.slingshot_anchor.x()
            self.active_bird.y = self.slingshot_anchor.y()
            
    def mousePressEvent(self, event):
        if self.game_state != 'playing':
            return
        if self.active_bird and not self.bird_in_flight:
            bird_screen_x = self.active_bird.x - self.camera_x
            bird_screen_y = self.active_bird.y
            dx = event.position().x() - bird_screen_x
            dy = event.position().y() - bird_screen_y
            if math.sqrt(dx*dx + dy*dy) < 40:
                self.dragging = True
                self.drag_pos = event.position()
                
    def mouseMoveEvent(self, event):
        if self.dragging and self.active_bird:
            self.drag_pos = event.position()
            anchor_screen = QPointF(self.slingshot_anchor.x() - self.camera_x,
                                   self.slingshot_anchor.y())
            dx = self.drag_pos.x() - anchor_screen.x()
            dy = self.drag_pos.y() - anchor_screen.y()
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > self.max_drag:
                scale = self.max_drag / dist
                dx *= scale
                dy *= scale
            self.active_bird.x = anchor_screen.x() + dx + self.camera_x
            self.active_bird.y = anchor_screen.y() + dy
            self.update()
            
    def mouseReleaseEvent(self, event):
        if self.dragging and self.active_bird:
            self.dragging = False
            anchor_screen = QPointF(self.slingshot_anchor.x() - self.camera_x,
                                   self.slingshot_anchor.y())
            dx = anchor_screen.x() - self.drag_pos.x()
            dy = anchor_screen.y() - self.drag_pos.y()
            
            speed = math.sqrt(dx*dx + dy*dy)
            if speed > 5:
                power = min(speed / self.max_drag, 1.0)
                launch_speed = power * 18
                angle = math.atan2(dy, dx)
                vx = math.cos(angle) * launch_speed
                vy = math.sin(angle) * launch_speed
                
                self.active_bird.x = self.slingshot_anchor.x()
                self.active_bird.y = self.slingshot_anchor.y()
                self.active_bird.launch(vx, vy)
                self.bird_in_flight = True
                self.current_bird_index += 1
                self.birds_changed.emit(len(self.bird_queue) - self.current_bird_index)
                
    def update_game(self):
        if self.game_state != 'playing':
            self.update()
            return
            
        self.anim_timer += 1
        h = self.height()
        self.ground_y = h - 80
        
        for p in self.particles[:]:
            if not p.update():
                self.particles.remove(p)
                
        for pig in self.pigs:
            pig.update()
            
        for block in self.blocks:
            block.update()
        
        if self.active_bird and self.bird_in_flight:
            self.active_bird.update()
            
            if self.active_bird.x - self.camera_x > self.width() * 0.6:
                self.target_camera_x = self.active_bird.x - self.width() * 0.6
                
            self.camera_x += (self.target_camera_x - self.camera_x) * 0.1
            
            bird = self.active_bird
            
            if bird.y > self.ground_y + 50 or bird.x > 2000 or bird.x < -200:
                self._on_bird_done()
                
            for pig in self.pigs:
                if not pig.alive:
                    continue
                dx = bird.x - pig.x
                dy = bird.y - pig.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < bird.radius + pig.radius:
                    killed = pig.take_damage(2)
                    if killed:
                        self._spawn_particles(pig.x, pig.y, QColor(100, 200, 100), 15)
                        self.score += 500 if pig.size == 'large' else (300 if pig.size == 'medium' else 200)
                        self.score_changed.emit(self.score)
                        self.pigs_changed.emit(sum(1 for p in self.pigs if p.alive))
                    else:
                        self._spawn_particles(pig.x, pig.y, QColor(150, 220, 150), 5)
                    bird.vx *= 0.3
                    bird.vy *= 0.3
                    
            for block in self.blocks:
                if not block.alive:
                    continue
                brect = block.get_rect()
                bx1, by1 = brect.x(), brect.y()
                bx2, by2 = brect.right(), brect.bottom()
                
                closest_x = max(bx1, min(bird.x, bx2))
                closest_y = max(by1, min(bird.y, by2))
                dx = bird.x - closest_x
                dy = bird.y - closest_y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < bird.radius:
                    damage = 1
                    if bird.bird_type == 'black':
                        damage = 3
                    elif bird.bird_type == 'yellow':
                        damage = 2
                    destroyed = block.take_damage(damage)
                    if destroyed:
                        mat_colors = {
                            'wood': QColor(180, 120, 60),
                            'stone': QColor(150, 150, 150),
                            'glass': QColor(150, 220, 255),
                            'ice': QColor(200, 240, 255)
                        }
                        color = mat_colors.get(block.material, QColor(200, 200, 200))
                        self._spawn_particles(bird.x, bird.y, color, 12)
                        self.score += 100
                        self.score_changed.emit(self.score)
                    
                    speed = math.sqrt(bird.vx**2 + bird.vy**2)
                    if dist > 0:
                        nx, ny = dx/dist, dy/dist
                        dot = bird.vx * nx + bird.vy * ny
                        bird.vx -= 2 * dot * nx * 0.5
                        bird.vy -= 2 * dot * ny * 0.5
                    bird.vx *= 0.6
                    bird.vy *= 0.6
                    
            if bird.y >= self.ground_y - bird.radius:
                bird.y = self.ground_y - bird.radius
                bird.vy *= -0.4
                bird.vx *= 0.8
                bird.bounce_count += 1
                if bird.bounce_count >= bird.max_bounces or abs(bird.vy) < 1:
                    self._on_bird_done()
                    
        alive_pigs = [p for p in self.pigs if p.alive]
        if not alive_pigs and self.game_state == 'playing':
            self.game_state = 'level_complete'
            self.score += max(0, (len(self.bird_queue) - self.current_bird_index)) * 1000
            self.score_changed.emit(self.score)
            self.game_over_signal.emit(True)
            
        if (self.active_bird is None and not self.bird_in_flight and 
                self.game_state == 'playing' and alive_pigs):
            self.game_state = 'game_over'
            self.game_over_signal.emit(False)
            
        self.update()
        
    def _on_bird_done(self):
        self.bird_in_flight = False
        self.camera_x = 0
        self.target_camera_x = 0
        self._place_next_bird()
        
    def _spawn_particles(self, x, y, color, count):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        self.ground_y = h - 80
        
        self._draw_background(painter, w, h)
        
        painter.save()
        painter.translate(-self.camera_x, 0)
        
        self._draw_ground(painter, w, h)
        self._draw_blocks(painter)
        self._draw_pigs(painter)
        self._draw_slingshot(painter)
        self._draw_bird_trail(painter)
        self._draw_bird(painter)
        self._draw_particles(painter)
        
        painter.restore()
        
        self._draw_aim_guide(painter)
        
        if self.game_state == 'level_complete':
            self._draw_overlay(painter, w, h, True)
        elif self.game_state == 'game_over':
            self._draw_overlay(painter, w, h, False)
            
    def _draw_background(self, painter, w, h):
        if self.theme == 'dark':
            sky_top = QColor(10, 10, 40)
            sky_bottom = QColor(30, 30, 80)
        else:
            sky_top = QColor(100, 180, 255)
            sky_bottom = QColor(200, 230, 255)
            
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, sky_top)
        grad.setColorAt(1, sky_bottom)
        painter.fillRect(0, 0, w, h, grad)
        
        if self.theme == 'dark':
            for sx, sy, size in self.stars:
                screen_x = (sx - self.camera_x * 0.1) % w
                alpha = int(150 + 100 * math.sin(self.anim_timer * 0.05 + sx))
                painter.setPen(QPen(QColor(255, 255, 255, alpha)))
                painter.drawEllipse(QPointF(screen_x, sy), size, size)
        else:
            for i in range(3):
                cx = (self.anim_timer * 0.3 + i * 300) % (w + 200) - 100
                cy = 60 + i * 40
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy), 60, 30)
                painter.drawEllipse(QPointF(cx + 40, cy - 10), 50, 25)
                painter.drawEllipse(QPointF(cx - 30, cy + 5), 45, 22)
                
    def _draw_ground(self, painter, w, h):
        gy = self.ground_y
        
        if self.theme == 'dark':
            ground_color = QColor(40, 80, 40)
            dirt_color = QColor(60, 40, 20)
        else:
            ground_color = QColor(80, 160, 60)
            dirt_color = QColor(140, 100, 60)
            
        painter.setBrush(QBrush(ground_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(int(-self.camera_x), int(gy), int(w + self.camera_x * 2 + 2000), int(h - gy))
        
        painter.setBrush(QBrush(dirt_color))
        painter.drawRect(int(-self.camera_x), int(gy + 20), int(w + self.camera_x * 2 + 2000), int(h - gy))
        
        painter.setBrush(QBrush(QColor(60, 140, 40)))
        for i in range(-10, 60):
            gx = i * 50 - (self.camera_x % 50)
            painter.drawEllipse(QPointF(gx, gy), 15, 8)
            
    def _draw_slingshot(self, painter):
        sx = self.slingshot_x
        sy = self.slingshot_y_base
        
        if self.theme == 'dark':
            wood_color = QColor(100, 70, 30)
        else:
            wood_color = QColor(139, 90, 43)
            
        painter.setPen(QPen(wood_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(sx), int(sy), int(sx), int(sy - 90))
        painter.drawLine(int(sx - 15), int(sy - 70), int(sx), int(sy - 90))
        painter.drawLine(int(sx + 15), int(sy - 70), int(sx), int(sy - 90))
        
        if self.active_bird and not self.bird_in_flight:
            anchor = self.slingshot_anchor
            bird_x = self.active_bird.x
            bird_y = self.active_bird.y
            
            if self.dragging:
                painter.setPen(QPen(QColor(80, 60, 40), 3))
                painter.drawLine(int(sx - 15), int(sy - 70), int(bird_x), int(bird_y))
                painter.drawLine(int(sx + 15), int(sy - 70), int(bird_x), int(bird_y))
            else:
                painter.setPen(QPen(QColor(80, 60, 40), 3))
                painter.drawLine(int(sx - 15), int(sy - 70), int(anchor.x()), int(anchor.y()))
                painter.drawLine(int(sx + 15), int(sy - 70), int(anchor.x()), int(anchor.y()))
        else:
            painter.setPen(QPen(QColor(80, 60, 40), 3))
            painter.drawLine(int(sx - 15), int(sy - 70), int(sx), int(sy - 90))
            painter.drawLine(int(sx + 15), int(sy - 70), int(sx), int(sy - 90))
            
    def _draw_bird_trail(self, painter):
        if self.active_bird and self.bird_in_flight:
            trail = self.active_bird.trail
            for i, (tx, ty) in enumerate(trail):
                alpha = int(255 * i / len(trail)) if trail else 0
                size = 3 * i / len(trail) if trail else 0
                painter.setBrush(QBrush(QColor(255, 200, 100, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(tx, ty), size, size)
                
    def _draw_bird(self, painter):
        if not self.active_bird:
            return
        bird = self.active_bird
        if not bird.alive:
            return
            
        painter.save()
        painter.translate(bird.x, bird.y)
        if self.bird_in_flight:
            painter.rotate(bird.rotation)
            
        r = bird.radius
        btype = bird.bird_type
        
        bird_colors = {
            'red': (QColor(220, 50, 50), QColor(180, 20, 20)),
            'blue': (QColor(80, 150, 255), QColor(40, 100, 220)),
            'yellow': (QColor(255, 220, 40), QColor(220, 180, 20)),
            'black': (QColor(60, 60, 60), QColor(20, 20, 20)),
            'white': (QColor(240, 240, 255), QColor(200, 200, 230)),
        }
        
        main_color, dark_color = bird_colors.get(btype, (QColor(200, 100, 100), QColor(160, 60, 60)))
        
        grad = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.2)
        grad.setColorAt(0, main_color.lighter(130))
        grad.setColorAt(0.6, main_color)
        grad.setColorAt(1, dark_color)
        
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(dark_color.darker(120), 1.5))
        painter.drawEllipse(QPointF(0, 0), r, r)
        
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(-r * 0.3, -r * 0.3), r * 0.3, r * 0.2)
        
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(0, 0, 0), 0.5))
        painter.drawEllipse(QPointF(r * 0.2, -r * 0.15), r * 0.2, r * 0.2)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(r * 0.25, -r * 0.2), r * 0.07, r * 0.07)
        
        if btype == 'red':
            painter.setBrush(QBrush(QColor(255, 100, 50)))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.moveTo(-r * 0.1, -r * 0.9)
            path.lineTo(-r * 0.4, -r * 0.5)
            path.lineTo(r * 0.2, -r * 0.6)
            path.closeSubpath()
            painter.drawPath(path)
            
            path2 = QPainterPath()
            path2.moveTo(r * 0.1, -r * 0.85)
            path2.lineTo(-r * 0.15, -r * 0.55)
            path2.lineTo(r * 0.35, -r * 0.6)
            path2.closeSubpath()
            painter.drawPath(path2)
            
        elif btype == 'yellow':
            painter.setBrush(QBrush(QColor(255, 140, 0)))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.moveTo(r * 0.4, -r * 0.1)
            path.lineTo(r * 1.1, r * 0.2)
            path.lineTo(r * 0.3, r * 0.3)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif btype == 'black':
            painter.setBrush(QBrush(QColor(255, 50, 50)))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.moveTo(0, -r * 1.0)
            path.lineTo(-r * 0.2, -r * 0.7)
            path.lineTo(r * 0.2, -r * 0.7)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif btype == 'white':
            painter.setBrush(QBrush(QColor(255, 200, 50)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(r * 0.1, r * 0.5), r * 0.35, r * 0.2)
            
        painter.setBrush(QBrush(QColor(255, 140, 0)))
        painter.setPen(QPen(QColor(200, 100, 0), 1))
        beak_path = QPainterPath()
        beak_path.moveTo(r * 0.4, 0)
        beak_path.lineTo(r * 0.9, r * 0.15)
        beak_path.lineTo(r * 0.4, r * 0.25)
        beak_path.closeSubpath()
        painter.drawPath(beak_path)
        
        painter.restore()
        
    def _draw_pigs(self, painter):
        for pig in self.pigs:
            if not pig.alive:
                continue
                
            wobble_offset = math.sin(self.anim_timer * 0.1) * (pig.wobble * 0.5)
            
            painter.save()
            painter.translate(pig.x + wobble_offset, pig.y)
            
            r = pig.radius
            
            if pig.damage_flash > 0:
                base_color = QColor(255, 100, 100)
                dark_color = QColor(200, 50, 50)
            else:
                health_ratio = pig.health / pig.max_health
                green_val = int(100 + 100 * health_ratio)
                base_color = QColor(60, green_val + 50, 60)
                dark_color = QColor(30, green_val, 30)
                
            grad = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.2)
            grad.setColorAt(0, base_color.lighter(130))
            grad.setColorAt(0.7, base_color)
            grad.setColorAt(1, dark_color)
            
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(dark_color.darker(130), 1.5))
            painter.drawEllipse(QPointF(0, 0), r, r)
            
            painter.setBrush(QBrush(base_color.lighter(110)))
            painter.setPen(QPen(dark_color, 1))
            painter.drawEllipse(QPointF(r * 0.25, -r * 0.1), r * 0.45, r * 0.35)
            
            painter.setBrush(QBrush(QColor(20, 20, 20)))
            painter.setPen(QPen(QColor(0, 0, 0), 0.5))
            painter.drawEllipse(QPointF(-r * 0.25, -r * 0.25), r * 0.2, r * 0.2)
            painter.drawEllipse(QPointF(r * 0.1, -r * 0.25), r * 0.2, r * 0.2)
            
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(-r * 0.22, -r * 0.3), r * 0.08, r * 0.08)
            painter.drawEllipse(QPointF(r * 0.13, -r * 0.3), r * 0.08, r * 0.08)
            
            painter.setBrush(QBrush(QColor(180, 100, 100)))
            painter.setPen(QPen(QColor(150, 70, 70), 1))
            painter.drawEllipse(QPointF(r * 0.3, r * 0.05), r * 0.22, r * 0.15)
            
            painter.setBrush(QBrush(QColor(20, 100, 20)))
            painter.setPen(Qt.PenStyle.NoPen)
            ear_path = QPainterPath()
            ear_path.moveTo(-r * 0.5, -r * 0.7)
            ear_path.lineTo(-r * 0.7, -r * 1.0)
            ear_path.lineTo(-r * 0.2, -r * 0.8)
            ear_path.closeSubpath()
            painter.drawPath(ear_path)
            
            ear_path2 = QPainterPath()
            ear_path2.moveTo(r * 0.1, -r * 0.75)
            ear_path2.lineTo(r * 0.0, -r * 1.05)
            ear_path2.lineTo(r * 0.4, -r * 0.85)
            ear_path2.closeSubpath()
            painter.drawPath(ear_path2)
            
            if pig.health < pig.max_health:
                painter.setPen(QPen(QColor(100, 50, 0), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                crack_count = pig.max_health - pig.health
                for c in range(crack_count):
                    angle = c * 120 * math.pi / 180
                    cx1 = math.cos(angle) * r * 0.3
                    cy1 = math.sin(angle) * r * 0.3
                    cx2 = math.cos(angle + 0.3) * r * 0.7
                    cy2 = math.sin(angle + 0.3) * r * 0.7
                    painter.drawLine(int(cx1), int(cy1), int(cx2), int(cy2))
                    
            painter.restore()
            
    def _draw_blocks(self, painter):
        for block in self.blocks:
            if not block.alive:
                continue
                
            rect = block.get_rect()
            
            if block.material == 'wood':
                if block.damage_flash > 0:
                    base = QColor(255, 180, 80)
                else:
                    base = QColor(180, 120, 60)
                dark = QColor(120, 70, 30)
                painter.setBrush(QBrush(base))
                painter.setPen(QPen(dark, 2))
                painter.drawRect(rect)
                
                painter.setPen(QPen(dark.lighter(120), 1))
                step = 15
                y = int(rect.y())
                while y < int(rect.bottom()):
                    painter.drawLine(int(rect.x()), y, int(rect.right()), y)
                    y += step
                    
            elif block.material == 'stone':
                if block.damage_flash > 0:
                    base = QColor(220, 220, 220)
                else:
                    base = QColor(140, 140, 150)
                dark = QColor(90, 90, 100)
                painter.setBrush(QBrush(base))
                painter.setPen(QPen(dark, 2))
                painter.drawRect(rect)
                
                painter.setPen(QPen(dark.lighter(115), 1))
                mid_x = int(rect.x() + rect.width() / 2)
                mid_y = int(rect.y() + rect.height() / 2)
                painter.drawLine(int(rect.x()), mid_y, int(rect.right()), mid_y)
                painter.drawLine(mid_x, int(rect.y()), mid_x, int(rect.bottom()))
                
            elif block.material == 'glass':
                if block.damage_flash > 0:
                    base = QColor(200, 240, 255, 200)
                else:
                    base = QColor(150, 220, 255, 160)
                dark = QColor(100, 180, 220, 200)
                painter.setBrush(QBrush(base))
                painter.setPen(QPen(dark, 1.5))
                painter.drawRect(rect)
                
                painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(rect.x() + 3, rect.y() + 3, 
                                       rect.width() * 0.3, rect.height() - 6))
                                       
            elif block.material == 'ice':
                if block.damage_flash > 0:
                    base = QColor(220, 245, 255, 220)
                else:
                    base = QColor(180, 230, 255, 200)
                dark = QColor(120, 190, 230, 220)
                painter.setBrush(QBrush(base))
                painter.setPen(QPen(dark, 1.5))
                painter.drawRect(rect)
                
                painter.setPen(QPen(QColor(200, 240, 255, 150), 1))
                painter.drawLine(int(rect.x() + 5), int(rect.y() + 5),
                               int(rect.right() - 5), int(rect.bottom() - 5))
                               
            if block.crack_level > 0:
                painter.setPen(QPen(QColor(80, 40, 0, 180), 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                cx = rect.center().x()
                cy = rect.center().y()
                for c in range(block.crack_level):
                    ang = c * 2.1 + 0.5
                    x1 = cx + math.cos(ang) * 5
                    y1 = cy + math.sin(ang) * 5
                    x2 = cx + math.cos(ang + 0.4) * min(rect.width(), rect.height()) * 0.4
                    y2 = cy + math.sin(ang + 0.4) * min(rect.width(), rect.height()) * 0.4
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                    
    def _draw_particles(self, painter):
        for p in self.particles:
            alpha = int(255 * p.life / p.max_life)
            color = QColor(p.color.red(), p.color.green(), p.color.blue(), alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            size = p.size * p.life / p.max_life
            painter.drawEllipse(QPointF(p.x, p.y), size, size)
            
    def _draw_aim_guide(self, painter):
        if self.dragging and self.active_bird:
            anchor_screen = QPointF(self.slingshot_anchor.x() - self.camera_x,
                                   self.slingshot_anchor.y())
            dx = anchor_screen.x() - self.drag_pos.x()
            dy = anchor_screen.y() - self.drag_pos.y()
            speed = math.sqrt(dx*dx + dy*dy)
            
            if speed > 5:
                power = min(speed / self.max_drag, 1.0)
                launch_speed = power * 18
                angle = math.atan2(dy, dx)
                vx = math.cos(angle) * launch_speed
                vy = math.sin(angle) * launch_speed
                
                painter.setPen(QPen(QColor(255, 255, 100, 150), 2, 
                                   Qt.PenStyle.DotLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                
                px, py = self.slingshot_anchor.x() - self.camera_x, self.slingshot_anchor.y()
                pvx, pvy = vx, vy
                
                for i in range(30):
                    pvy += 0.4
                    px += pvx
                    py += pvy
                    if py > self.ground_y:
                        break
                    size = 3 - i * 0.08
                    if size > 0:
                        alpha = int(200 - i * 6)
                        painter.setBrush(QBrush(QColor(255, 255, 100, max(0, alpha))))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(QPointF(px, py), max(0.5, size), max(0.5, size))
                        
    def _draw_overlay(self, painter, w, h, success):
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)
        
        if success:
            color = QColor(255, 220, 50)
            text = "LEVEL COMPLETE! 🎉"
        else:
            color = QColor(255, 80, 80)
            text = "GAME OVER 💀"
            
        painter.setPen(QPen(color))
        font = QFont("Arial", max(20, w // 25), QFont.Weight.Bold)
        painter.setFont(font)
        
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        painter.drawText(int((w - text_w) / 2), int(h / 2 - 20), text)
        
        score_text = f"Score: {self.score}"
        font2 = QFont("Arial", max(14, w // 40))
        painter.setFont(font2)
        painter.setPen(QPen(QColor(255, 255, 255)))
        fm2 = QFontMetrics(font2)
        sw = fm2.horizontalAdvance(score_text)
        painter.drawText(int((w - sw) / 2), int(h / 2 + 30), score_text)
        
    def set_theme(self, theme):
        self.theme = theme
        self.update()
        
    def next_level(self):
        self.level += 1
        self.setup_level(self.level)
        
    def restart(self):
        self.score = 0
        self.level = 1
        self.score_changed.emit(0)
        self.setup_level(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'
        self.current_lang = 'en'
        self.setWindowTitle("Angry Bird")
        self.setMinimumSize(800, 600)
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._build_top_bar()
        self._build_game_area()
        self._build_bottom_bar()
        
        self.apply_theme()
        self.update_texts()
        
    def _build_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 5, 15, 5)
        top_layout.setSpacing(15)
        
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Arial", 20, QFont.Weight.Bold)
        self.title_label.setFont(font)
        
        self.score_label = QLabel()
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.level_label = QLabel()
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.birds_label = QLabel()
        self.birds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.pigs_label = QLabel()
        self.pigs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Light', 'Dark'])
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'فارسی', '中文'])
        self.lang_combo.currentTextChanged.connect(self._on_lang_change)
        
        top_layout.addWidget(self.title_label, 2)
        top_layout.addWidget(self.score_label, 1)
        top_layout.addWidget(self.level_label, 1)
        top_layout.addWidget(self.birds_label, 1)
        top_layout.addWidget(self.pigs_label, 1)
        top_layout.addStretch(1)
        top_layout.addWidget(self.theme_combo)
        top_layout.addWidget(self.lang_combo)
        
        self.main_layout.addWidget(self.top_bar)
        
    def _build_game_area(self):
        self.canvas = GameCanvas()
        self.canvas.score_changed.connect(self._on_score_change)
        self.canvas.game_over_signal.connect(self._on_game_over)
        self.canvas.birds_changed.connect(self._on_birds_change)
        self.canvas.pigs_changed.connect(self._on_pigs_change)
        self.main_layout.addWidget(self.canvas, 1)
        
    def _build_bottom_bar(self):
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(55)
        bot_layout = QHBoxLayout(self.bottom_bar)
        bot_layout.setContentsMargins(15, 5, 15, 5)
        bot_layout.setSpacing(15)
        
        self.hint_label = QLabel()
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.restart_btn = QPushButton()
        self.restart_btn.setFixedSize(120, 38)
        self.restart_btn.clicked.connect(self._on_restart)
        
        self.next_btn = QPushButton()
        self.next_btn.setFixedSize(120, 38)
        self.next_btn.clicked.connect(self._on_next_level)
        self.next_btn.setVisible(False)
        
        bot_layout.addWidget(self.hint_label, 3)
        bot_layout.addStretch(1)
        bot_layout.addWidget(self.restart_btn)
        bot_layout.addWidget(self.next_btn)
        
        self.main_layout.addWidget(self.bottom_bar)
        
    def _on_theme_change(self, text):
        self.current_theme = 'dark' if text == 'Dark' else 'light'
        self.canvas.set_theme(self.current_theme)
        self.apply_theme()
        
    def _on_lang_change(self, text):
        if text == 'فارسی':
            self.current_lang = 'fa'
        elif text == '中文':
            self.current_lang = 'zh'
        else:
            self.current_lang = 'en'
        self.update_texts()
        
    def _on_score_change(self, score):
        t = TRANSLATIONS[self.current_lang]
        self.score_label.setText(f"{t['score']}: {score}")
        
    def _on_game_over(self, success):
        t = TRANSLATIONS[self.current_lang]
        if success:
            self.next_btn.setVisible(True)
            self.next_btn.setText(t['next_level'])
        else:
            self.next_btn.setVisible(False)
            
    def _on_birds_change(self, count):
        t = TRANSLATIONS[self.current_lang]
        self.birds_label.setText(f"{t['birds_left']}: {count}")
        
    def _on_pigs_change(self, count):
        t = TRANSLATIONS[self.current_lang]
        self.pigs_label.setText(f"{t['pigs_left']}: {count}")
        
    def _on_restart(self):
        self.canvas.restart()
        self.next_btn.setVisible(False)
        self.update_texts()
        
    def _on_next_level(self):
        self.canvas.next_level()
        self.next_btn.setVisible(False)
        self.update_texts()
        
    def update_texts(self):
        t = TRANSLATIONS[self.current_lang]
        self.title_label.setText(t['title'])
        self.score_label.setText(f"{t['score']}: {self.canvas.score}")
        self.level_label.setText(f"{t['level']}: {self.canvas.level}")
        birds_left = max(0, len(self.canvas.bird_queue) - self.canvas.current_bird_index)
        self.birds_label.setText(f"{t['birds_left']}: {birds_left}")
        pigs_left = sum(1 for p in self.canvas.pigs if p.alive)
        self.pigs_label.setText(f"{t['pigs_left']}: {pigs_left}")
        self.hint_label.setText(t['drag_to_aim'])
        self.restart_btn.setText(t['restart'])
        if self.next_btn.isVisible():
            self.next_btn.setText(t['next_level'])
            
    def apply_theme(self):
        if self.current_theme == 'dark':
            bg = "#1a1a2e"
            bar_bg = "#16213e"
            text_color = "#e0e0ff"
            btn_bg = "#0f3460"
            btn_hover = "#e94560"
            btn_text = "#ffffff"
            combo_bg = "#0f3460"
            combo_text = "#e0e0ff"
            border_color = "#0f3460"
        else:
            bg = "#f0f4ff"
            bar_bg = "#4a90d9"
            text_color = "#ffffff"
            btn_bg = "#2ecc71"
            btn_hover = "#27ae60"
            btn_text = "#ffffff"
            combo_bg = "#ffffff"
            combo_text = "#333333"
            border_color = "#3498db"
            
        self.central.setStyleSheet(f"background-color: {bg};")
        
        self.top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {bar_bg};
                border-bottom: 2px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }}
            QComboBox {{
                background-color: {combo_bg};
                color: {combo_text};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 90px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {combo_bg};
                color: {combo_text};
                selection-background-color: {border_color};
            }}
        """)
        
        self.bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {bar_bg};
                border-top: 2px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 12px;
                background: transparent;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {border_color};
            }}
        """)
        
        self.title_label.setStyleSheet(f"""
            font-size: {max(16, self.width() // 45)}px;
            font-weight: bold;
            color: #FFD700;
            background: transparent;
        """)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.title_label.setStyleSheet(f"""
            font-size: {max(16, self.width() // 45)}px;
            font-weight: bold;
            color: #FFD700;
            background: transparent;
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Angry Bird")
    
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.resize(1000, 680)
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
