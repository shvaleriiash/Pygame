import os
import random
import sys
from itertools import cycle
import pickle

import pygame

pygame.init()


GRAVITY = 0.1


KILL_BUTTERFLY = pygame.USEREVENT + 1
KILL_BUTTERFLY_EVENT = pygame.event.Event(KILL_BUTTERFLY)

ADD_SCORE = pygame.USEREVENT + 2
ADD_SCORE_EVENT = pygame.event.Event(ADD_SCORE)

ADD_COIN = pygame.USEREVENT + 3
ADD_COIN_EVENT = pygame.event.Event(ADD_COIN)


def load_audio() -> dict:
    sounds = {}
    sound_prefix = "venv/data/audio/"
    if "win" in sys.platform:
        sound_prefix += "wav/"
    else:
        sound_prefix += "ogg/"
    for file_name in os.listdir(sound_prefix):
        sound = pygame.mixer.Sound(sound_prefix + file_name)
        sound.set_volume(0.1)
        sounds[file_name.split(".")[0]] = sound
    return sounds


SOUNDS = load_audio()


def load_image(fullname: str) -> pygame.Surface:
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def load_animations(prefix: str) -> cycle:
    animations = []
    prefix = os.path.join("venv/data/sprites", prefix)
    for name in os.listdir(prefix):
        path = os.path.join(prefix, name)
        if os.path.isfile(path):
            animations.append(load_image(path))
    return cycle(animations)


class Background(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, backgrounds)
        self.images = {
            "day": load_image("venv/data/sprites/back_ground/day.png"),
            "night": load_image("venv/data/sprites/back_ground/night.png"),
        }
        self.image = self.images["day"]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = 2

    def change_image(self, time_of_day: str):
        self.image = self.images[time_of_day]
        self.mask = pygame.mask.from_surface(self.image)

    def set_x(self, x_pos: float):
        self.rect.x = x_pos

    def update(self):
        if self.rect.x <= -self.rect.width:
            self.rect.x = self.rect.width
        self.rect.x -= self.speed


class Coin(pygame.sprite.Sprite):
    def __init__(self, x_pos, y_pos):
        super().__init__(all_sprites, coins)
        self.anim = load_animations("coins")
        self.image = next(self.anim)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x_pos
        self.rect.y = y_pos
        self.transform()

        self.speed = 2

        self.start_tick = pygame.time.get_ticks()

    def update(self):
        seconds = (pygame.time.get_ticks() - self.start_tick) / 1000
        if seconds > 0.1:
            self.image = next(self.anim)
            self.mask = pygame.mask.from_surface(self.image)
            self.transform()
            x, y = self.rect.centerx, self.rect.y
            self.rect = self.image.get_rect()
            self.rect.centerx, self.rect.y = x, y
            self.start_tick = pygame.time.get_ticks()

        if self.rect.x < -self.rect.width:
            self.kill()
        self.rect.x -= self.speed

    def transform(self):
        self.image = pygame.transform.scale(
            self.image,
            (self.image.get_rect().width // 4, self.image.get_rect().height // 4),
        )
        self.mask = pygame.mask.from_surface(self.image)


class BasePipe(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, pipes)
        self.images = {
            "day": load_image("venv/data/sprites/pipes/day.png"),
            "night": load_image("venv/data/sprites/pipes/night.png"),
        }
        self.image = self.images["day"]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.speed = 2
        self.skylight = 100  # расстояние между лианами
        self.used = False

    def change_image(self, time_of_day: str):
        self.image = self.images[time_of_day]
        self.mask = pygame.mask.from_surface(self.image)

    def set_coin(self):
        Coin(self.rect.x - 23, self.rect.y - self.skylight // 2 - 12)

    def set_x(self, x_pos):
        self.rect.x = x_pos

    def update(self):
        if not self.used and self.rect.x < 144:
            pygame.event.post(ADD_SCORE_EVENT)
            self.used = True
        if self.rect.x < -self.rect.width:
            self.kill()
        self.rect.x -= self.speed


class DownPipe(BasePipe):
    def __init__(self):
        super().__init__()
        self.set_y()

    def set_y(self):
        self.rect.y = random.randint(200, 350)


class UpPipe(BasePipe):
    def __init__(self, down_x, down_y):
        super().__init__()
        self.images["day"] = pygame.transform.flip(self.images["day"], False, True)
        self.images["night"] = pygame.transform.flip(self.images["night"], False, True)
        self.image = self.images["day"]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = down_x
        self.rect.y = down_y - self.skylight - self.rect.height

    def update(self):
        if not self.used and self.rect.x < 144:
            self.used = True
        if self.rect.x < -self.rect.width:
            self.kill()
        self.rect.x -= self.speed


class Ground(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__(all_sprites, grounds)
        self.images = {
            "day": load_image("venv/data/sprites/ground/day.png"),
            "night": load_image("venv/data/sprites/ground/night.png"),
        }
        self.image = self.images["day"]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.y = 400
        self.speed = 2

    def change_image(self, time_of_day: str):
        self.image = self.images[time_of_day]
        self.mask = pygame.mask.from_surface(self.image)

    def set_x(self, x_pos: float):
        self.rect.x = x_pos

    def update(self):
        if self.rect.x <= -self.rect.width:
            self.rect.x = self.rect.width
        self.rect.x -= self.speed


class Butterfly(pygame.sprite.Sprite):

    def __init__(self, color):
        super().__init__(all_sprites)
        self.color = color
        self.anim = load_animations("butterflies/" + self.color)
        self.image = next(self.anim)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = 144 - self.rect.width // 2
        self.rect.y = 256 - self.rect.height // 2
        self.velocity = 0

        self.start_tick = pygame.time.get_ticks()

    def update(self):
        for coin in coins:
            if pygame.sprite.collide_mask(self, coin):
                coin.kill()
                pygame.event.post(ADD_COIN_EVENT)

        ground_collided = pygame.sprite.spritecollide(self, grounds, False)
        pygame.sprite.spritecollide(self, pipes, False)

        if ground_collided:
            pygame.event.post(KILL_BUTTERFLY_EVENT)

        for pipe in pipes:
            if pygame.sprite.collide_mask(self, pipe):
                pygame.event.post(KILL_BUTTERFLY_EVENT)

        self.velocity -= GRAVITY
        seconds = (pygame.time.get_ticks() - self.start_tick) / 1000

        if seconds > 0.1:
            self.image = next(self.anim)
            self.mask = pygame.mask.from_surface(self.image)
            self.start_tick = pygame.time.get_ticks()

        if self.rect.y <= 0:
            self.velocity = -15 * GRAVITY

        self.rect.y -= self.velocity

    def jump(self):
        SOUNDS["wing"].play()
        self.velocity = 2

    def change_color(self, color):
        self.color = color
        self.anim = load_animations("butterflies/" + self.color)
        self.image = next(self.anim)
        self.mask = pygame.mask.from_surface(self.image)


class Text(pygame.sprite.Sprite):

    def __init__(self, x_finish, y_finish, name):
        super().__init__()
        self.image = load_image(name)
        self.rect = self.image.get_rect()
        self.x_finish = x_finish
        self.rect.y = y_finish
        self.rect.x = -self.rect.width
        self.speed = 10
        self.end = False

    def update(self):
        if self.rect.x < self.x_finish:
            self.rect.move_ip(self.speed, 0)
        else:
            self.end = True

    def renew(self):
        self.rect.x = -self.rect.width
        self.end = False
        self.speed = 10
        self.end = False


class Button(pygame.sprite.Sprite):

    def __init__(self, x_finish, y_finish, name):
        super().__init__()
        self.image = load_image(name)
        self.rect = self.image.get_rect()
        self.x_finish = x_finish
        self.rect.y = y_finish
        self.rect.x = -self.rect.width
        self.speed = 10
        self.end = False

    def check(self) -> True:
        return self.rect.collidepoint(*pygame.mouse.get_pos())

    def transform(self, size):
        y_pos = self.rect.y
        self.image = pygame.transform.scale(self.image, size)
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = -self.rect.width
        self.rect.y = y_pos

    def update(self):
        if self.rect.x < self.x_finish:
            self.rect.move_ip(self.speed, 0)
        else:
            self.end = True

    def renew(self):
        self.rect.x = -self.rect.width
        self.end = False


class Score:
    def __init__(self, score, y_pos):
        self.score = score
        self.y_pos = y_pos
        self.images = {
            file_name[0]: load_image("venv/data/sprites/nums/" + file_name)
            for file_name in os.listdir("venv/data/sprites/nums")
        }
        self.digits = []

    def __add__(self, other):
        self.score += other

    def refresh(self):
        self.digits.clear()
        n = 0
        for num in str(self.score):
            digit = pygame.sprite.Sprite()
            digit.image = self.images[num]
            digit.rect = digit.image.get_rect()
            digit.rect.x = digit.image.get_width() * n
            digit.rect.y = self.y_pos
            n += 1
            self.digits.append(digit)

    def show(self):
        for digit in self.digits:
            screen.blit(digit.image, digit.rect)


all_sprites = pygame.sprite.Group()
pipes = pygame.sprite.Group()
backgrounds = pygame.sprite.Group()
grounds = pygame.sprite.Group()
coins = pygame.sprite.Group()
nums = pygame.sprite.Group()

# шрифт
pygame.font.init()
FONT = pygame.font.SysFont("Comic Sans MS", 15)

# название и иконка
pygame.display.set_caption("FLUTTER")
pygame.display.set_icon(load_image("venv/data/sprites/ico/ico.ico"))

clock = pygame.time.Clock()

screen = pygame.display.set_mode((288, 512))
surface = pygame.Surface((288, 512), pygame.SRCALPHA)

Background()
b = Background()
b.set_x(b.rect.width)

Ground()
g = Ground()
g.set_x(g.rect.width)
butterfly = Butterfly("green")


class GameHandler:
    def __init__(self):
        self.game_mode = "MENU"
        self.prefix = "venv/data/sprites/texts/"
        # загрузка спрайтов
        self.over = Text(48, 235, self.prefix + "gameover.png")
        self.title = Text(55, 50, self.prefix + "title.png")
        self.get_ready = Text(52, 150, self.prefix + "get_ready.png")
        self.button_shop = Button(163, 390, self.prefix + "shop.png")
        # self.button_color = Button(94, 80, self.prefix + "color.png")
        self.button_menu = Button(94, 180, self.prefix + "menu.png")
        self.button_reset = Button(102, 100, self.prefix + "reset.png")
        self.button_sett = Button(10, 390, self.prefix + "settings.png")
        self.butterfly_green_button = Button(10, 130, "venv/data/sprites/butterflies/green/1.png")
        self.butterfly_blue_button = Button(100, 130, "venv/data/sprites/butterflies/blue/1.png")
        self.butterfly_purple_button = Button(201, 130, "venv/data/sprites/butterflies/purple/1.png")

        self.button_shop.transform((150, 100))
        self.button_reset.transform((150, 100))
        self.button_menu.transform((150, 100))
        self.button_sett.transform((150, 100))

        self.score = Score(0, 0)

        self.high_score, self.coins, color, self.shop_bought = self.load_data()
        butterfly.change_color(color)

        self.high_score_text = FONT.render(
            f"High score: {self.high_score}", False, (255, 255, 255)
        )
        self.color = pygame.Color(120, 0, 255, 50)


        self.coins_text = FONT.render(f"Coins: {self.coins}", False, (255, 255, 255))
        self.bought_text = FONT.render("Bought", False, (255, 255, 255))
        self.price_text1 = FONT.render("50 coins", False, (255, 255, 255))
        self.price_text2 = FONT.render("100 coins", False, (255, 255, 255))
        self.color_text = FONT.render(f"Color: {int(self.color.hsva[0]), (self.color.hsva[0])}", False, (255, 255, 255))

        self.time = random.choice(["day", "night"])

        for background in backgrounds:
            background.change_image(self.time)
        for ground in grounds:
            ground.change_image(self.time)
        SOUNDS["swoosh"].play()

    @staticmethod
    def load_data() -> tuple:
        with open("venv/data/data.fbd", "rb") as f:
            data = pickle.load(f)
        return data

    def save_data(self):
        with open("venv/data/data.fbd", "wb") as f:
            pickle.dump((self.high_score, self.coins, butterfly.color, self.shop_bought), f)

    def terminate(self):
        self.save_data()
        pygame.quit()
        sys.exit()

    def rect(self):
        pygame.draw.rect(surface, self.color, pygame.Rect(0, 0, 288, 512))
        screen.blit(surface, (0, 0))

    def start(self):
        while True:
            clock.tick(60)
            if self.game_mode == "MENU":
                self.game_mode = self.main_menu()
            elif self.game_mode == "GAME":
                self.game_mode = self.game()
            elif self.game_mode == "OVER":
                self.game_mode = self.game_over()
            elif self.game_mode == "SHOP":
                self.game_mode = self.shop()
            elif self.game_mode == "RESET":
                self.game_mode = self.reset()
            elif self.game_mode == "SETTINGS":
                self.game_mode = self.settings()

    def game_over(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()

        if self.over.end:  # Проверка, закончило ли изображение перемещение
            self.over.renew()
            pygame.time.wait(2000)
            for pipe in pipes:
                pipe.kill()
            for coin in coins:
                coin.kill()

            # Обновление спрайтов
            butterfly.rect.y = 256 - butterfly.rect.height // 2
            self.time = random.choice(["day", "night"])
            self.high_score_text = FONT.render(
                f"High score: {self.high_score}", False, (255, 255, 255
            ))
            self.coins_text = FONT.render(f"Coins: {self.coins}", False, (255, 255, 255))
            for background in backgrounds:
                background.change_image(self.time)
            for ground in grounds:
                ground.change_image(self.time)
            return "MENU"

        self.over.update()

        all_sprites.draw(screen)
        nums.draw(screen)
        grounds.draw(screen)
        self.rect()
        screen.blit(butterfly.image, butterfly.rect)
        screen.blit(butterfly.image, butterfly.rect)
        screen.blit(self.over.image, self.over.rect)
        screen.blit(self.high_score_text, (20, 475))

        pygame.display.update()

        return "OVER"

    def main_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Старт
                    self.title.renew()
                    self.get_ready.renew()
                    self.button_shop.renew()
                    self.button_reset.renew()
                    self.button_menu.renew()
                    self.button_sett.renew()
                    butterfly.jump()
                    self.score.refresh()
                    for i in range(5):
                        dp = DownPipe()
                        dp.rect.x = 300 + dp.rect.x + 200 * i
                        if random.choices([True, False], k=1, weights=[1, 3])[0]:
                            dp.set_coin()
                        up = UpPipe(dp.rect.x, dp.rect.y)
                        dp.change_image(self.time)
                        up.change_image(self.time)
                    for background in backgrounds:
                        background.change_image(self.time)
                    for ground in grounds:
                        ground.change_image(self.time)
                    return "GAME"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_shop.check():  # нажатие кнопки shop
                    butterfly.rect.x = -100
                    SOUNDS["swoosh"].play()
                    return "SHOP"
                if self.button_sett.check():  # нажатие кнопки reset
                    butterfly.rect.x = -100
                    SOUNDS["swoosh"].play()
                    return "SETTINGS"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.color = tuple(map(int, input('введите цвет в rgba').split()))

        if not self.title.end:
            self.title.update()

        if not self.button_shop.end:
            self.button_shop.update()

        if not self.button_reset.end:
            self.button_reset.update()

        if not self.button_menu.end:
            self.button_menu.update()

        if not self.button_sett.end:
            self.button_sett.update()

        if not self.get_ready.end:
            self.get_ready.update()

        all_sprites.draw(screen)
        self.rect()
        screen.blit(butterfly.image, butterfly.rect)
        screen.blit(self.title.image, self.title.rect)
        screen.blit(self.get_ready.image, self.get_ready.rect)
        screen.blit(self.button_shop.image, self.button_shop.rect)
        screen.blit(self.button_sett.image, self.button_sett.rect)

        pygame.display.update()
        return "MENU"

    def choose_sprite(self, color):
        butterfly.change_color(color)
        butterfly.rect.x = 144 - butterfly.rect.width // 2
        self.butterfly_green_button.renew()
        self.butterfly_purple_button.renew()
        self.butterfly_blue_button.renew()
        SOUNDS["swoosh"].play()

    def shop(self):
        txts = [
            (self.bought_text, 25, 210),
            (self.bought_text if self.shop_bought[1] else self.price_text1, 110, 210),
            (self.bought_text if self.shop_bought[2] else self.price_text2, 215, 210),
        ]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if all(
                    [
                        self.butterfly_green_button.end,
                        self.butterfly_blue_button.end,
                        self.butterfly_purple_button.end,
                    ]
                ):
                    if self.butterfly_purple_button.check():
                        if self.shop_bought[2]:
                            self.choose_sprite("purple")
                            return "MENU"
                        else:
                            if self.coins >= 100:
                                self.coins -= 100
                                self.shop_bought[2] = True
                                SOUNDS["bought"].play()
                    if self.butterfly_green_button.check():
                        if self.shop_bought[0]:
                            self.choose_sprite("green")
                            return "MENU"
                    if self.butterfly_blue_button.check():
                        if self.shop_bought[1]:
                            self.choose_sprite("blue")
                            return "MENU"
                        else:
                            if self.coins >= 50:
                                self.coins -= 50
                                self.shop_bought[1] = True
                                SOUNDS["bought"].play()

        if not self.butterfly_green_button.end:
            self.butterfly_green_button.update()

        if not self.butterfly_blue_button.end:
            self.butterfly_blue_button.update()

        if not self.butterfly_purple_button.end:
            self.butterfly_purple_button.update()

        self.coins_text = FONT.render(f"Coins: {self.coins}", False, (255, 255, 255))
        all_sprites.draw(screen)
        self.rect()
        screen.blit(butterfly.image, butterfly.rect)
        screen.blit(self.butterfly_green_button.image, self.butterfly_green_button.rect)
        screen.blit(self.butterfly_blue_button.image, self.butterfly_blue_button.rect)
        screen.blit(self.butterfly_purple_button.image, self.butterfly_purple_button.rect)
        screen.blit(self.coins_text, (20, 475))

        for t in txts:
            screen.blit(t[0], (t[1], t[2]))

        pygame.display.update()
        return "SHOP"

    def game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    butterfly.jump()
            elif event.type == ADD_COIN:
                self.coins += 1
                SOUNDS["collect_coin"].play()
            elif event.type == KILL_BUTTERFLY:
                SOUNDS["hit"].play()
                SOUNDS["die"].play()
                butterfly.velocity = 0
                if self.score.score > self.high_score:
                    self.high_score = self.score.score
                    self.high_score_text = FONT.render(
                        f"High score: {self.high_score}", False, (255, 255, 255)
                    )
                self.score.score = 0
                return "OVER"
            elif event.type == ADD_SCORE:
                SOUNDS["point"].play()
                dp = DownPipe()
                dp.rect.x = 150 + dp.rect.x + 200 * 5
                up = UpPipe(dp.rect.x, dp.rect.y)
                dp.change_image(self.time)
                up.change_image(self.time)
                if random.choices([True, False], k=1, weights=[1, 3])[0]:
                    dp.set_coin()
                self.score + 1
                self.score.refresh()
        all_sprites.update()
        all_sprites.draw(screen)
        grounds.draw(screen)
        self.rect()
        screen.blit(butterfly.image, butterfly.rect)
        self.score.show()
        pygame.display.update()
        return "GAME"

    def reset(self):
        with open("venv/data/data.fbd", "wb") as f:
            pickle.dump((0, 0, butterfly.color, [True, False, False]), f)

        if not self.butterfly_green_button.end:
            self.butterfly_green_button.update()

        if not self.butterfly_blue_button.end:
            self.butterfly_blue_button.update()

        if not self.butterfly_purple_button.end:
            self.butterfly_purple_button.update()

        pygame.display.update()
        main()
        return "RESET"

    def settings(self):
        hsv = self.color.hsva
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_reset.check():
                    SOUNDS["swoosh"].play()
                    return "RESET"
                if self.button_menu.check():
                    SOUNDS["swoosh"].play()
                    return "MENU"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.color.hsva = ((hsv[0] - 5) % 360, hsv[1], hsv[2], hsv[3])
                elif event.key == pygame.K_RIGHT:
                    self.color.hsva = ((hsv[0] + 5) % 360, hsv[1], hsv[2], hsv[3])
                elif event.key == pygame.K_UP:
                    self.color.hsva = (hsv[0], hsv[1], hsv[2], (hsv[3] + 5) % 100)
                elif event.key == pygame.K_DOWN:
                    self.color.hsva = (hsv[0], hsv[1], hsv[2], (hsv[3] - 5) % 100)

        if not self.butterfly_green_button.end:
            self.butterfly_green_button.update()

        if not self.butterfly_blue_button.end:
            self.butterfly_blue_button.update()

        if not self.butterfly_purple_button.end:
            self.butterfly_purple_button.update()

        self.color_text = FONT.render(f"Color: {int(self.color.hsva[0]), int(self.color.hsva[3])}",
                                      False, (255, 255, 255))
        all_sprites.draw(screen)
        self.rect()
        screen.blit(butterfly.image, butterfly.rect)

        screen.blit(self.button_reset.image, self.button_reset.rect)
        screen.blit(self.button_menu.image, self.button_menu.rect)
        screen.blit(self.coins_text, (20, 435))
        screen.blit(self.high_score_text, (20, 455))
        screen.blit(self.color_text, (20, 475))

        pygame.display.update()
        return "SETTINGS"


def main():
    game = GameHandler()
    game.start()


if __name__ == "__main__":
    main()