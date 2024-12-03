import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))
NUM_OF_BOMBS = 5


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

class Explosion:
    def __init__(self, obj):
        """
        explosion クラスのイニシャライザを設定
        """
        self.ex_img_lst = [
            pg.image.load("fig/explosion.gif"),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True)
            ]
        # 爆発の位置をオブジェクトの中心に合わせる
        self.rct = self.ex_img_lst[0].get_rect()
        self.rct.center = obj.rct.center
        self.life = 120  # 爆発の寿命

    def update(self, screen):
        """
        爆発の表示を制御
        """
        self.life -= 1
        if self.life >= 0:
            # lifeの値に応じて交互に爆発画像を選択し描画する
            img = self.ex_img_lst[self.life % len(self.ex_img_lst)]
            screen.blit(img, self.rct)

class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5,0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)
        if sum_mv != [0,0]:
            self.dire = sum_mv

# ビームクラス:
class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.img = pg.transform.rotozoom(self.img, angle, 0.9)
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 5 # self.ビームの左座標 = こうかとんの右座標
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5# self.ビームの中心縦座標 = こうかとんの中心縦座標

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)   


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        スコアクラスの初期設定
        色、フォントなどを決めている
        """
        self.fonto = pg.font.SysFont("hgp創英角ポップ体", 30)
        self.font_color = (0, 0, 255)
        self.point = 0
        self.img = self.fonto.render(f"score : {self.point}", 0, self.font_color)
        self.x = 100
        self.y = HEIGHT-50

    def update(self, screen):
        """
        スコアの表示に関する処理を行うメソッド
        現在のスコアを表示させる文字列Sarfaceを生成し、スクリーンにblitする
        """
        # スコアが変化した後にスコア表示Surfaceを再生成
        self.img = self.fonto.render(f"score : {self.point}", 0, self.font_color)
        # スコアをスクリーンにblit
        screen.blit(self.img, (self.x, self.y))

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    #ボムを複数生成するためのリストを作成
    bombs = [Bomb((255, random.randint(0, 255), random.randint(0, 255)), 10) for _ in range(NUM_OF_BOMBS)]
    clock = pg.time.Clock()
    tmr = 0
    beams = []
    score = Score()
    ex_lst = []
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))
        screen.blit(bg_img, [0, 0])

        for bomb in bombs:
            if bomb:#こうかとんと爆弾の衝突判定
                if bird.rct.colliderect(bomb.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                    bird.change_img(8, screen)
                    #gameoverという文字をblit
                    fonto = pg.font.Font(None, 80)
                    txt = fonto.render("Game Over", True, (255, 0, 0))
                    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                    pg.display.update()
                    time.sleep(1)
                    return

        # ビームと爆弾の衝突判定
        for beam in beams:
            if beam:
                beam.update(screen)
                for n, bomb in enumerate(bombs):
                    if bomb and beam.rct.colliderect(bomb.rct):
                        # 衝突が発生した場合の処理
                        ex_lst.append(Explosion(bomb))
                        bombs[n] = None
                        beams.remove(beam)  # 衝突したビームをリストから削除
                        score.point += 1
                        break  # 複数の爆弾に対して同時に衝突を処理しないためにループを抜ける

        for bomb in bombs:
            if bomb:#こうかとんと爆弾の衝突判定
                if bird.rct.colliderect(bomb.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                    bird.change_img(8, screen)
                    pg.display.update()
                    time.sleep(1)
                    return

        for beam in beams:
            if beam:#ビームと爆弾の衝突判定 , 
                beam.update(screen)
                #リストの要素１つ１つに対して、ビームとの衝突判定を行う
                for n, bomb in enumerate(bombs):
                    if bomb:
                        if beam.rct.colliderect(bomb.rct):
                            bombs[n] = None

        beams = [beam for beam in beams if beam is not None]
        bombs = [bomb for bomb in bombs if bomb is not None]
        beams = [beam for beam in beams if beam.rct.right <= WIDTH]

        for bomb in bombs:
            if bomb:
                bomb.update(screen)

        for ex in ex_lst:
            ex.update(screen) 
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        score.update(screen)#スコアの表示
        pg.display.update()
        tmr += 1
        clock.tick(50)
        # print(len(beams))#ビームの数チェック用

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
    # print("a")