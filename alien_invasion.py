# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 17:48:18 2021

@author: YalinCheng
"""

import sys
from time import sleep
import pygame
from settings import Settings
from game_stats import GameStats
from ship import Ship
from bullet import Bullet
from alien import Alien
from button import Button
from scoreboard import Scoreboard

class AlienInvasion:
    """管理游戏资源和行为的类"""
    
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.settings = Settings()
        
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        # full screen
        #self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        #self.settings.screen_height = self.screen.get_rect().height
        #self.settings.screen_width = self.screen.get_rect().width
        
        pygame.display.set_caption("Alien Invasion")
        
        # 创建存储游戏统计信息的实例
        #   并创建记分牌
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.play_button = Button(self, "Play")
        
        self._create_fleet()
    
    def run_game(self):
        """开始游戏主循环"""
        while True:
            self._check_events()
            
            if self.stats.game_active:
                self.ship.update()         
                self._update_bullets()
                self._update_aliens()
                
            self._update_screen()
    
    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._check_mouse_events(event)
    
    def _check_keydown_events(self, event):
        # 响应按键
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
    
    def _check_keyup_events(self, event):
        # 响应松开
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False
    
    def _check_mouse_events(self, event):
        mouse_pos = pygame.mouse.get_pos()
        self._check_play_button(mouse_pos)
        
    def _fire_bullet(self):
        """创建一个子弹，加入编组 bullets 中"""
        if len(self.bullets) < self.settings.bullet_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
    
    def _update_bullets(self):
        """更新子弹的位置并删除消失的子弹"""
        # 更新子弹位置
        self.bullets.update()            
        # 删除消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        #print(len(self.bullets))
        self._check_bullet_alien_collisions()
    
    def _check_bullet_alien_collisions(self):
        """响应子弹和外星人碰撞"""
        # 删除发生碰撞的子弹和外星人
        collisions = pygame.sprite.groupcollide(
                self.bullets, self.aliens, True, True)
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
                self.sb.prep_score()
                self.sb.check_high_score()
        
        if not self.aliens:
            # 删除所有子弹并创建新的外星人群
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()
            
            # 提高等级
            self.stats.level += 1
            self.sb.prep_level()
    
    def _create_alien(self, alien_number, row_number):
        # 创建第一个外星人并加入当前行
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)
    
    def _create_fleet(self):
        """创建外星人群"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_alien_x = available_space_x // (2 * alien_width)
        
        # 计算可容纳多少行外星人
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - 
                             3 * alien_height - ship_height)
        number_rows = available_space_y // (2 * alien_height)
        
        # 创建群
        for row_number in range(number_rows):
            for alien_number in range(number_alien_x):
                self._create_alien(alien_number, row_number)
    
    def _check_fleet_edges(self):
        """所有外星人到达边缘时采取措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        """将整体外星人下移，并改变方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1
    
    def _update_aliens(self):
        """更新外星人群中所有外星人位置"""
        self._check_fleet_edges()
        self.aliens.update()
                
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
            
        self._check_aliens_bottom()
    
    def _ship_hit(self):
        """响应飞船被外星人撞击"""
        if self.stats.ships_left > 0:
            # 减少飞船剩余数量
            self.stats.ships_left -= 1
            self.sb.prep_ships()
        
            # 清空屏幕剩余外星人和子弹
            self.aliens.empty()
            self.bullets.empty()
        
            # 创建新的外星人群，将飞船置于初始位置
            self._create_fleet()
            self.ship.center_ship()
        
            # 暂停
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)
    
    def _check_aliens_bottom(self):
        """检查外星人是否到达屏幕底端"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break
    
    def _check_play_button(self, mouse_pos):
        """在玩家单机 Play 按钮时开始游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.stats.game_active = True
            self.stats.reset_stats()
            
            self.aliens.empty()
            self.bullets.empty()
            
            self._create_fleet()
            self.ship.center_ship()
            self.settings.initialize_dynamic_settings()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            
            pygame.mouse.set_visible(False)
    
    def _update_screen(self):
        """更新主屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        
        if not self.stats.game_active:
            self.play_button.draw_button()
        else:
            self.ship.blitme()
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.aliens.draw(self.screen)
            self.sb.show_score()            
            
        # 让最近绘制的屏幕可见
        pygame.display.flip()
    
if __name__ == '__main__':
    # 创建游戏实例并运行
    ai = AlienInvasion()
    ai.run_game()