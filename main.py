# -*- coding: utf-8 -*-
# Blaster
# Version: 0.3.0
# Copyright (C) 2016, KeyWeeUsr(Peter Badida) <keyweeusr@gmail.com>
# License: GNU GPL v3.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# More info in LICENSE.txt
#
# The above copyright notice, warning and additional info together with
# LICENSE.txt file shall be included in all copies or substantial portions
# of the Software.

# levels will be in json format(blocks)

import json
import random
import os.path as op
from os import listdir
from functools import partial

from kivy import require
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
require('1.9.2')
'''
App.map without breakable: (left -> right)
[[0,0,0,0,0],     bottom(y=0)
 [0,2,0,2,0],       |
 [0,0,0,0,0],       |
 [0,2,0,2,0],       v
 [0,0,0,0,0]      top(y=top)
]
'''


class Game(ScreenManager):
    '''Root widget of the game.'''
    def __init__(self, **kw):
        super(Game, self).__init__(**kw)
        self.transition = SlideTransition(direction='up')
        self.current = 'menu'


class Wall(Image):
    '''Basic block for a game - borders, columns, breakable, background.'''
    def __init__(self, **kw):
        super(Wall, self).__init__(**kw)
        self.app = App.get_running_app()
        self.text = kw.get('text', '')
        self.place = kw.get('place', '')


class Bomber(Wall):
    '''Player with stats. Always spawns at [0, 0].'''

    def __init__(self, **kw):
        super(Bomber, self).__init__(**kw)
        self.app = App.get_running_app()
        self.app.player = self
        self.gate = None
        self.move_dt = 0
        self.extra = None
        self.place = [0, 0]
        self.move_clock = None
        self.bombwalking = False
        self.default_pos = [50, 50]
        self.keyboard = Window.request_keyboard(self.keyboard_close, self)
        self.keyboard.bind(on_key_down=self.on_keyboard_down)
        self.keyboard.bind(on_key_up=self.on_key_up)
        self.move()

    def die(self):
        print 'dead'
        return
        # still incomplete
        self.reset_stats()
        self.app.level.reset_level()

    def reset_stats(self):
        '''Reset stats here - e.g. death, level reset, etc.'''
        # save highscore, last level to stats.json
        self.gate = None
        self.extra = None
        self.place = [0, 0]
        self.pos = self.default_pos
        self.bombwalking = False
        self.source = 'stand1.png'
        self.move_clock = None
        self.move_dt = 0
        # # reset level: - do in Level class
        # self.app.map
        # self.app.breakable
        # self.app.touchable
        # container.scroll_x&scroll_y = 0
        # remove from self.app.level.ids.lvlwindow everything except Bomber
        pass

    def collide_npc(self):
        '''Collision with npc i.e. death handling.'''
        for t in self.app.touchable:
            if t.place == self.place:
                self.die()

    def collide_extra(self):
        '''Collision with extra item.'''
        if self.pos == self.extra.pos:
            print 'extra'

    def collide_gate(self):
        '''Collision with gate - level end.'''
        if self.pos == self.gate.pos:
            print 'gate'

    def get_movement(self, direction, dt):
        self.move_dt += dt
        if self.move_dt > 1:
            Clock.unschedule(self.move_clock)
            self.move_dt = 0
            self.move()
            return
        if direction not in self.source:
            self.source = direction+'1.png'
        stage = int(self.source.replace(direction, '').replace('.png', ''))
        if stage != 2:
            self.source = direction + str(stage+1) + '.png'
        else:
            self.source = direction + '1.png'

    def move(self, direction='stand'):
        if self.move_clock:
            Clock.unschedule(self.move_clock)
        self.move_clock = partial(self.get_movement, direction)
        Clock.schedule_interval(self.move_clock, .15)

    def update_pos(self, direction):
        '''Walking function.'''
        self.move(direction)
        if direction == 'up' and self.pos[1] < self.arch['size'][1]:
            if self.get_block(direction):
                self.place[1] += 1
                self.pos = self.pos[0], self.pos[1] + 50
        elif direction == 'down' and self.pos[1] > 50:
            if self.get_block(direction):
                self.place[1] -= 1
                self.pos = self.pos[0], self.pos[1] - 50
        elif direction == 'left' and self.pos[0] > 50:
            if self.get_block(direction):
                self.place[0] -= 1
                self.pos = self.pos[0] - 50, self.pos[1]
        elif direction == 'right' and self.pos[0] < self.arch['size'][0]:
            if self.get_block(direction):
                self.place[0] += 1
                self.pos = self.pos[0] + 50, self.pos[1]
        self.app.level.ids.container.scroll_to(self, padding=160)
        self.collide_npc()
        self.collide_extra()
        self.collide_gate()

    def get_block(self, direction):
        '''
        Get block from 2D array to check if there is something
        in front of the player.
        '''
        if direction == 'up':
            if not self.app.map[self.place[1]+1][self.place[0]]:
                return True
        elif direction == 'down':
            if not self.app.map[self.place[1]-1][self.place[0]]:
                return True
        elif direction == 'left':
            if not self.app.map[self.place[1]][self.place[0]-1]:
                return True
        elif direction == 'right':
            if not self.app.map[self.place[1]][self.place[0]+1]:
                return True

    def keyboard_close(self):
        self.keyboard.unbind(on_key_down=on_keyboard_down)
        self.keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        '''Do something when a key is pressed.'''
        # continuous smooth movement later
        if keycode[1] == 'up' or keycode[1] == 'w':
            self.update_pos('up')
        elif keycode[1] == 'down' or keycode[1] == 's':
            self.update_pos('down')
            self.move('down')
        elif keycode[1] == 'left' or keycode[1] == 'a':
            self.update_pos('left')
            self.move('left')
        elif keycode[1] == 'right' or keycode[1] == 'd':
            self.update_pos('right')
            self.move('right')
        elif keycode[1] == 'spacebar':
            self.parent.add_widget(Bomb(pos=self.pos, place=self.place[:]))
            if not self.bombwalking:
                self.app.map[self.place[1]][self.place[0]] = 1
        elif keycode[1] == 'enter':
            pass
        elif keycode[1] == 'escape':
            exit()
        elif keycode[1] == 'p':
            pass  # self.pause_game() that pauses Clocks
        return True

    def on_key_up(self, keyboard, keycode):
        '''Do something when a key is released.'''
        if keycode[1] == 'up' or keycode[1] == 'w':
            pass
        elif keycode[1] == 'down' or keycode[1] == 's':
            pass
        elif keycode[1] == 'left' or keycode[1] == 'a':
            pass
        elif keycode[1] == 'right' or keycode[1] == 'd':
            pass


class Bonus(object):
    '''
    An item which will spawn in a wall and will be highlighted
    at the end of a level.(Extra item)
    '''
    pass


class Monster(Wall):
    '''Monster instance. Will take form&stats from json(probably).'''
    def __init__(self, **kw):
        super(Monster, self).__init__(**kw)
        self.source = 'a1.png'
        self.stage = 1
        self.gif = Clock.schedule_interval(self.sparkle, 0.15)

    def sparkle(self, dt):
        '''Changing pictures of a gate.'''
        self.source = 'a'+str(self.stage)+'.png'
        if self.stage == 2:
            self.stage = 1
        else:
            self.stage += 1


class Gate(Wall):
    '''An exit from level'''
    def __init__(self, **kw):
        super(Gate, self).__init__(**kw)
        self.source = 'gate/gate1.png'
        self.stage = 1
        self.gif = Clock.schedule_interval(self.sparkle, 0.15)

    def sparkle(self, dt):
        '''Changing pictures of a gate.'''
        self.source = 'gate/gate'+str(self.stage)+'.png'
        if self.stage == 4:
            self.stage = 1
        else:
            self.stage += 1


class Column(Wall):
    '''
    Concrete, non-destroyable block.
    Block fire widgets only, or the fire too?
    '''
    def __init__(self, **kw):
        super(Column, self).__init__(**kw)
        self.source = 'column.png'


class Fire(Wall):  # pun, hehe
    '''
    Fire, spawns after a bomb explodes, changes image over time and collides
    with player (and maybe other bombs).
    '''
    def __init__(self, **kw):
        super(Fire, self).__init__(**kw)
        self.stage = 0
        self.dir = kw.get('dir', '')
        self.burn()
        Clock.schedule_interval(self.burn, .1)

    def burn(self, dt=0):
        # kill player staying on the bomb
        # if self.place == self.app.player.place:
        #     self.app.player.die()
        if self.stage == 6:
            Clock.unschedule(self.burn)
            self.parent.remove_widget(self)
        if self.dir == '':
            self.source = 'fire/' + str(self.stage) + 'c.png'
        elif self.dir == 'up':
            self.source = 'fire/' + str(self.stage) + 'eu.png'
        elif self.dir == 'down':
            self.source = 'fire/' + str(self.stage) + 'ed.png'
        elif self.dir == 'left':
            self.source = 'fire/' + str(self.stage) + 'el.png'
        elif self.dir == 'right':
            self.source = 'fire/' + str(self.stage) + 'er.png'
        elif self.dir == 'ud':
            self.source = 'fire/' + str(self.stage) + 'ud.png'
        elif self.dir == 'lr':
            self.source = 'fire/' + str(self.stage) + 'lr.png'
        self.stage += 1


class Bomb(Wall):
    '''
    A bomb which will spawn when player <space>. Clock, then boom.
    '''
    def __init__(self, **kw):
        super(Bomb, self).__init__(**kw)
        self.source = 'bomb1.png'
        self.time = 300
        self.range = kw.get('range', 3)
        self.tick = Clock.schedule_interval(self.countdown, 1)
        self.gif = Clock.schedule_interval(self.sparkle, 0.25)

    def sparkle(self, dt):
        '''Changing pictures of a bomb to make the knot burning.'''
        if self.source != 'bomb2.png' and not self.time % 12.5:
            self.source = 'bomb2.png'
        else:
            if self.source != 'bomb1.png':
                self.source = 'bomb1.png'

    def countdown(self, dt):
        '''Countdown until the bomb detonates and spawns Fire widgets'''
        self.time -= 100
        if not self.time > 0:
            Clock.unschedule(self.tick)
            x, y = [p/50 - 1 for p in self.pos]
            self.app.map[y][x] = 0
            self.fire()
            self.destroy()
            self.parent.remove_widget(self)

    def clear(self, breakable, r, purge=False):
        if r == 'purge':
            for r in xrange(len(self.app.breakable)):
                try:
                    if (breakable[r].place[0] == 'x' and
                            breakable[r].place[1] == 'x'):
                        breakable.remove(breakable[r])
                except IndexError:
                    pass
            self.app.breakable = breakable[:]
            return
        breakable[r].place[0] = 'x'
        breakable[r].place[1] = 'x'

    def fire(self):
        self.parent.add_widget(Fire(pos=self.pos, place=self.place))

    def kill_player(self, place):
        if self.app.player.place == place:
            self.app.player.die()

    def destroy(self):
        i = self.app.breakable[:]
        g_pos = [g_pos/50-1 for g_pos in self.pos]  # [0,0] left down
        where = ['up', 'down', 'right', 'left']  # fire directions(max 1 shot)
        # replace with single characters
        cnt = 1
        while where:
            if cnt <= self.range or not where:
                for r in xrange(len(self.app.breakable)):
                    # check if flame hits column first(blocks fire range)
                    # up and right need to be at the bottom, or IndexError
                    try:
                        if self.app.map[g_pos[1]][g_pos[0] - cnt] == 2:
                            if 'left' in where:
                                where.remove('left')
                        if self.app.map[g_pos[1] - cnt][g_pos[0]] == 2:
                            if 'down' in where:
                                where.remove('down')
                        if self.app.map[g_pos[1] + cnt][g_pos[0]] == 2:
                            if 'up' in where:
                                where.remove('up')
                        if self.app.map[g_pos[1]][g_pos[0] + cnt] == 2:
                            if 'right' in where:
                                where.remove('right')
                    except IndexError:
                        pass  # end of map

                    # check if flame hits breakable wall
                    if ((g_pos[0] + cnt == i[r].place[0]) and
                            (g_pos[1] == i[r].place[1]) and
                            ('right' in where)):
                        where.remove('right')
                        self.app.map[g_pos[1]][g_pos[0]+cnt] = 0
                        fire_right = Fire(pos=[self.pos[0] + 50 * cnt,
                                               self.pos[1]],
                                          dir='right',
                                          place=[self.place[0] + cnt,
                                                 self.place[1]])
                        self.parent.add_widget(fire_right)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] - cnt == i[r].place[0]) and
                            (g_pos[1] == i[r].place[1]) and
                            ('left' in where)):
                        where.remove('left')
                        self.app.map[g_pos[1]][g_pos[0]-cnt] = 0
                        fire_left = Fire(pos=[self.pos[0] - 50 * cnt,
                                              self.pos[1]],
                                         dir='left',
                                         place=[self.place[0] - cnt,
                                                self.place[1]])
                        self.parent.add_widget(fire_left)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] == i[r].place[0]) and
                            (g_pos[1] + cnt == i[r].place[1]) and
                            ('up' in where)):
                        where.remove('up')
                        self.app.map[g_pos[1] + cnt][g_pos[0]] = 0
                        fire_up = Fire(pos=[self.pos[0],
                                            self.pos[1] + 50 * cnt],
                                       dir='up',
                                       place=[self.place[0],
                                              self.place[1] + cnt])
                        self.parent.add_widget(fire_up)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] == i[r].place[0]) and
                            (g_pos[1] - cnt == i[r].place[1]) and
                            ('down' in where)):
                        where.remove('down')
                        self.app.map[g_pos[1] - cnt][g_pos[0]] = 0
                        fire_down = Fire(pos=[self.pos[0],
                                              self.pos[1] - 50 * cnt],
                                         dir='down',
                                         place=[self.place[0],
                                                self.place[1] - cnt])
                        self.parent.add_widget(fire_down)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)

                # check for borders and increase
                pos_up = self.pos[1] + 50 * cnt
                pos_down = self.pos[1] - 50 * cnt
                pos_right = self.pos[0] + 50 * cnt
                pos_left = self.pos[0] - 50 * cnt
                border_up = self.app.player.arch['size'][1] + 50
                border_right = self.app.player.arch['size'][0] + 50

                if pos_up < border_up and 'up' in where:
                    place_up = [self.place[0], self.place[1] + cnt]
                    fire_ud = Fire(pos=[self.pos[0], pos_up],
                                   dir='ud' if cnt != self.range else 'up',
                                   place=place_up)
                    self.kill_player(place_up)
                    self.parent.add_widget(fire_ud)

                if pos_down > 0 and 'down' in where:
                    place_down = [self.place[0], self.place[1] - cnt]
                    fire_ud = Fire(pos=[self.pos[0], pos_down],
                                   dir='ud' if cnt != self.range else 'down',
                                   place=place_down)
                    self.kill_player(place_down)
                    self.parent.add_widget(fire_ud)

                if pos_right < border_right and 'right' in where:
                    place_right = [self.place[0] + cnt, self.place[1]]
                    fire_lr = Fire(pos=[pos_right, self.pos[1]],
                                   dir='lr' if cnt != self.range else 'right',
                                   place=place_right)
                    self.kill_player(place_right)
                    self.parent.add_widget(fire_lr)

                if pos_left > 0 and 'left' in where:
                    place_left = [self.place[0] - cnt, self.place[1]]
                    fire_lr = Fire(pos=[pos_left, self.pos[1]],
                                   dir='lr' if cnt != self.range else 'left',
                                   place=place_left)
                    self.kill_player(place_left)
                    self.parent.add_widget(fire_lr)
                cnt += 1
            else:
                self.clear(i, 'purge')
                del i
                break


class Level(Screen):
    '''Level screen'''
    def __init__(self, **kw):
        super(Level, self).__init__(**kw)
        self.app = App.get_running_app()
        self.path = self.app.path
        self.app.level = self
        self.app.breakable = []  # Walls
        self.app.touchable = []  # NPC
        self.stats = None
        self.hashes = None
        self.texture = Image(source='grass.png').texture
        self.texture.wrap = 'repeat'

    def create_hashes(self):
        if not op.exists(self.app.user_data_dir+'/hash.tiff'):
            from hashlib import md5
            self.hashes = []
            for i in listdir(self.app.path+'/levels'):
                with open(self.app.path+'/levels/'+i) as f:
                    passw = str(md5(f.read()).hexdigest()).upper()[:8]
                    self.hashes.append(passw)
            with open(self.app.user_data_dir+'/hash.tiff', 'w') as f:
                f.write('\n'.join(self.hashes))
        else:
            with open(self.app.user_data_dir+'/hash.tiff') as f:
                self.hashes = f.read().split('\n')

    def load_level(self, start=False, password=None):
        '''Json loading'''
        if not op.exists(self.app.user_data_dir+'/stats.json'):
            self.stats = {'highscore': 0, 'last_level': 0}
            with open(self.app.user_data_dir+'/stats.json', 'w') as f:
                f.write(json.dumps(self.stats))
        else:
            with open(self.app.user_data_dir+'/stats.json') as f:
                self.stats = json.load(f)
        self.create_hashes()
        if not password:
            with open(self.path+'/levels/1.json') as f:
                self.set_level(json.load(f))
                self.manager.current = 'level'
        else:
            with open(self.path+'/levels/'+str(level)+'.json') as f:
                self.set_level(json.load(f))
                self.manager.current = 'level'

    def create_borders(self, arch):
        # border size
        border_top = (arch['size'][0] + 100) / 50
        border_left = (arch['size'][1]) / 50
        border_right = border_left
        border_bottom = border_top
        width = arch['size'][0]
        height = arch['size'][1]

        # border spawn
        for top in xrange(border_top):
            self.ids.lvlwindow.add_widget(Column(pos=[50*top, height+50]))
        for left in xrange(border_left):
            self.ids.lvlwindow.add_widget(Column(pos=[0, 50+50*left]))
        for right in xrange(border_right):
            self.ids.lvlwindow.add_widget(Column(pos=[width+50, 50+50*right]))
        for bot in xrange(border_bottom):
            self.ids.lvlwindow.add_widget(Column(pos=[50*bot, 0]))
        self.create_columns(arch, border_left, border_top)

    def create_columns(self, arch, border_left, border_top):
        block_left = border_left - int(str(arch['size'][1])[:-2]) - 1
        block_top = border_top - int(str(arch['size'][0])[:-2]) - 3
        for h in xrange(block_left):
            for w in xrange(block_top):
                col = Column(pos=[100+w*100, 100+h*100])
                self.ids.lvlwindow.add_widget(col)

    def set_level(self, arch):
        '''
        Setting the level architecture from json:
            width x height
            id of extra + count
            id of npc + count
            boss maybe?
        '''
        self.app.player.arch = arch
        # increase the size of level by borders + move it
        self.ids.lvlwindow.size_hint = None, None
        self.ids.lvlwindow.size = [i + 100 for i in arch['size']]
        self.ids.lvlwindow.pos = [p + 50 for p in self.ids.lvlwindow.pos]
        self.create_borders(arch)

        # spawn npc somewhere
        # minimum_pos [50, 50]
        # maximum_pos [ arch['size'][0], arch['size'][1] ]
        npc_top = arch['size'][0] / 50
        npc_left = arch['size'][1] / 50
        # generate zero map
        self.app.map = [[0 for x in xrange(npc_top)] for y in range(npc_left)]
        for h in xrange(npc_left):
            for w in xrange(npc_top):
                # leave out wall
                if self.roll() and ((h+1) % 2 or (w+1) % 2):
                    wall = Wall(text='[%s, %s]' % (w, h),
                                pos=[50+50*w, 50+50*h],
                                place=[w, h])
                    self.app.map[h][w] = 1
                    self.app.breakable.append(wall)
                    self.ids.lvlwindow.add_widget(wall)
                elif not (h+1) % 2 and not (w+1) % 2:
                    # unbreakable blocks(columns)
                    self.app.map[h][w] = 2
        self.spawn('gate')
        self.spawn('extra')
        self.spawn_npc(arch['npc'], arch['c_npc'], arch['size'])

    def roll(self, percent=20):
        '''Simple random counter'''
        return random.randrange(100) < percent

    def spawn(self, what, count=1):
        if what == 'gate':
            random.shuffle(self.app.breakable)
            x, y = self.app.breakable.pop().place
            gate_pos = [50 + 50 * x, 50 + 50 * y]
            gate = Gate(pos=gate_pos, place=[x, y])
            wall = Wall(pos=gate_pos, place=[x, y])
            self.app.map[y][x] = 1
            self.app.breakable.append(wall)
            self.app.player.gate = gate
            self.ids.lvlwindow.add_widget(gate)
            self.ids.lvlwindow.add_widget(wall)
        elif what == 'extra':
            random.shuffle(self.app.breakable)
            while True:
                temp = self.app.breakable.pop()
                x, y = temp.place
                extra_pos = [50 + 50 * x, 50 + 50 * y]
                if extra_pos != self.app.player.gate.pos:
                    break
                else:
                    if temp not in self.app.breakable:
                        self.app.breakable.append(temp)
            extra = Wall(pos=extra_pos, color=[0, 1, 0, 1], place=[x, y])
            wall = Wall(pos=extra_pos, place=[x, y])
            self.app.map[y][x] = 1
            self.app.breakable.append(wall)
            self.app.player.extra = extra
            self.ids.lvlwindow.add_widget(extra)
            self.ids.lvlwindow.add_widget(wall)
        elif what == 'boss':
            pass

    def spawn_npc(self, type=None, count=0, borders=None):
        while count > 0:
            x = random.randint(0, borders[0]/50-1)
            y = random.randint(0, borders[1]/50-1)
            pos_x, pos_y = [i*50+50 for i in [x, y]]
            for b in self.app.breakable:
                if not [x, y] == b.place and not self.app.map[y][x] >= 1:
                    if [x, y] == [0, 0]:
                        break
                    npc = Monster(pos=[pos_x, pos_y],
                                  place=[x, y])
                    self.app.touchable.append(npc)
                    self.ids.lvlwindow.add_widget(npc)
                    count -= 1
                    break

    def reset_level(self):
        pass


class Menu(Screen):
    def __init__(self, **kw):
        self.app = App.get_running_app()
        self.level = self.app.level
        super(Menu, self).__init__(**kw)

    def start_game(self):
        self.level.load_level(True)

    def load_game(self):
        self.level.load_level()


class Blaster(App):
    path = op.dirname(op.abspath(__file__))

    def build(self):
        return Game()

if __name__ == '__main__':
    Blaster().run()
