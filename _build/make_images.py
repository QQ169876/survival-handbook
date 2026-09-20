# -*- coding: utf-8 -*-
"""生成《穿越生存手册》全部示意图（PNG），纯 PIL 绘制，含中文标注。"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r"D:\穿越生存手册\图片"
os.makedirs(OUT, exist_ok=True)
F_BOLD = "C:/Windows/Fonts/simhei.ttf"
F_REG = "C:/Windows/Fonts/simhei.ttf"


def f(sz):
    return ImageFont.truetype(F_BOLD, sz)


def new(w, h, title):
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 120, 120), width=2)
    d.text((18, 14), title, font=f(24), fill=(0, 0, 0))
    d.line([18, 48, w - 18, 48], fill=(150, 150, 150), width=2)
    return im, d


def box(d, x, y, w, h, text, fill=(235, 243, 250), outline=(40, 90, 140), fs=18):
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=2)
    # 居中文字（先按原有换行拆分，再按宽度折行）
    lines = []
    for seg in text.split("\n"):
        seg = seg.strip()
        if seg:
            lines.extend(wrap(seg, max(1, int(w / fs))))
    lines = [ln for ln in lines if ln][:5]
    total = len(lines) * (fs + 4)
    ty = y + (h - total) / 2
    for ln in lines:
        tw = d.textlength(ln, font=f(fs))
        d.text((x + (w - tw) / 2, ty), ln, font=f(fs), fill=(0, 0, 0))
        ty += fs + 4


def wrap(text, per):
    """按字符数粗暴折行"""
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= per:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out[:4]


def arrow(d, p1, p2, color=(30, 30, 30), width=3):
    d.line([p1, p2], fill=color, width=width)
    import math
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    L = 10
    a1 = (p2[0] - L * math.cos(ang - 0.4), p2[1] - L * math.sin(ang - 0.4))
    a2 = (p2[0] - L * math.cos(ang + 0.4), p2[1] - L * math.sin(ang + 0.4))
    d.polygon([p2, a1, a2], fill=color)


def label(d, x, y, text, fs=16, color=(0, 0, 0), fill=None):
    if fill is not None:
        color = fill
    d.text((x, y), text, font=f(fs), fill=color)


def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p)
    print("saved", p)


# ---------------------------------------------------------------
# 1. 青霉素制备流程
def img_penicillin():
    im, d = new(1000, 620, "图1-1  青霉素土法制备流程（表面培养法）")
    steps = [
        ("① 选种", "柑橘/西瓜/馒头上的\n青绿色绒状霉"),
        ("② 培养基", "米汤+糖+豆粉\n煮沸灭菌"),
        ("③ 接种培养", "25~27℃避光\n静置5~7天"),
        ("④ 过滤", "细布+木炭+砂层\n除菌体"),
        ("⑤ 酸化", "加醋调pH2.5~3"),
        ("⑥ 吸附", "活性炭吸附\n再碱液洗脱"),
        ("⑦ 低温浓缩", "水浴<60℃\n浓缩成稠膏"),
        ("⑧ 干燥存用", "摊薄阴干\n避光密封"),
    ]
    x0, y0, bw, bh, gap = 40, 90, 105, 110, 12
    for i, (t, s) in enumerate(steps):
        col = i % 4
        row = i // 4
        x = x0 + col * (bw + gap + 8)
        y = y0 + row * (bh + 90)
        box(d, x, y, bw, bh, t + "\n" + s, fill=(232, 244, 236), outline=(40, 120, 70), fs=14)
        if col < 3:
            arrow(d, (x + bw + 2, y + bh / 2), (x + bw + gap + 6, y + bh / 2))
        if row == 0 and col == 3:
            arrow(d, (x0 + bw / 2, y + bh + 4), (x0 + bw / 2, y + bh + 60))
            label(d, x0 + bw / 2 + 10, y + bh + 20, "转入下一阶段", fs=14, color=(90, 90, 90))
    label(d, 40, 540, "要点：青霉是需氧菌，必须浅盘静置培养（液深≤3cm），黑暗处25℃左右最佳；", fs=17)
    label(d, 40, 566, "黄绿色、黑绿色霉多为曲霉/其他杂菌，不可用；全程忌油忌肥皂接触。", fs=17, color=(170, 40, 40))
    save(im, "01_青霉素流程.png")


# 2. 过滤与吸附装置剖面
def img_filter():
    im, d = new(1000, 560, "图1-2  发酵液过滤与吸附装置（可直接照做）")
    # 漏斗形容器
    d.polygon([(120, 120), (420, 120), (330, 330), (210, 330)], fill=(245, 245, 235), outline=(60, 60, 60), width=3)
    label(d, 150, 140, "陶盆/木桶\n（上口大）", fs=16)
    # 滤层
    layers = [("细麻布（4层）", (250, 250, 250)), ("洗净细砂（厚度5cm）", (235, 225, 190)),
              ("碎木炭（吸附杂质）", (90, 90, 90)), ("细麻布（承托）", (250, 250, 250))]
    y = 170
    for name, col in layers:
        d.rectangle([(160, y), (380, y + 32)], fill=col, outline=(60, 60, 60), width=2)
        label(d, 395, y + 8, name, fs=16)
        y += 34
    d.line([(270, 330), (270, 400)], fill=(60, 60, 60), width=3)
    d.ellipse([(180, 400), (360, 500)], fill=(230, 245, 250), outline=(40, 90, 140), width=3)
    label(d, 205, 440, "接液陶罐", fs=18)
    label(d, 620, 150, "操作顺序：", fs=20)
    for i, t in enumerate(["1. 发酵液先静置，取上层清液", "2. 缓慢倒入，勿搅动滤层",
                           "3. 初滤液再滤一遍", "4. 滤液加醋调酸后过活性炭柱",
                           "5. 木炭用碱液（草木灰水）洗脱", "6. 洗脱液低温浓缩成膏"]):
        label(d, 620, 190 + i * 32, t, fs=16)
    label(d, 120, 520, "提示：木炭须先蒸煮再焙干，否则带入杂菌；所有容器用沸水烫过再使用。", fs=16, color=(150, 60, 20))
    save(im, "02_过滤装置.png")


# 3. 草木灰淋滤制碱（制皂用）
def img_lye():
    im, d = new(1000, 560, "图2-1  草木灰淋滤制碱液（制皂第一步）")
    # 木桶
    d.polygon([(180, 130), (520, 130), (500, 400), (200, 400)], fill=(230, 220, 200), outline=(80, 60, 30), width=3)
    label(d, 230, 150, "木桶/陶缸（底部钻孔）", fs=16)
    d.rectangle([(200, 200), (500, 260)], fill=(150, 150, 150), outline=(60, 60, 60), width=2)
    label(d, 250, 220, "草木灰（硬木灰最佳）压实", fs=16, fill=(255, 255, 255))
    d.rectangle([(200, 180), (500, 198)], fill=(200, 220, 240), outline=(60, 60, 60), width=2)
    label(d, 250, 182, "上层铺稻草/麻布作过滤层", fs=14)
    d.text((560, 180), "缓慢浇入清水/雨水\n（忌用硬井水）", font=f(16), fill=(0, 0, 80))
    arrow(d, (555, 195), (505, 195), color=(0, 80, 160))
    # 滴水
    for i in range(3):
        d.ellipse([(330 + i * 30, 405), (340 + i * 30, 420)], fill=(120, 170, 220))
    d.polygon([(280, 440), (480, 440), (460, 520), (300, 520)], fill=(235, 245, 250), outline=(40, 90, 140), width=3)
    label(d, 310, 465, "接碱液（KOH/K₂CO₃）", fs=17)
    label(d, 560, 260, "浓度检验（鸡蛋浮沉法）：", fs=18)
    label(d, 560, 292, "• 新鲜鸡蛋放入碱液，露出硬币大小（约Ø2cm）", fs=15)
    label(d, 560, 320, "  → 碱度合适，可用来煮油制皂", fs=15)
    label(d, 560, 348, "• 沉底 = 太稀，须回淋再浓缩", fs=15)
    label(d, 560, 376, "• 漂浮过多 = 太浓，加水稀释（易伤手）", fs=15)
    label(d, 120, 60, "安全：碱液腐蚀皮肤，操作戴布手套，溅入眼立即用大量清水冲洗（醋水更佳）。", fs=16, color=(170, 30, 30))
    save(im, "03_草木灰淋滤.png")


# 4. 香水蒸馏装置
def img_distill():
    im, d = new(1000, 600, "图3-1  水蒸气蒸馏法制香水/精油")
    # 加热炉
    d.rectangle([(120, 430), (330, 520)], fill=(190, 190, 190), outline=(60, 60, 60), width=3)
    label(d, 140, 455, "炭火炉", fs=17)
    d.rectangle([(150, 430), (300, 430)], fill=(220, 120, 40), width=1)
    # 蒸馏锅
    d.ellipse([(150, 300), (330, 430)], fill=(215, 225, 235), outline=(50, 70, 90), width=3)
    label(d, 165, 350, "铜/陶蒸馏锅\n（花材+水）", fs=16)
    # 导汽管
    d.line([(300, 315), (430, 250), (430, 200)], fill=(80, 80, 80), width=6)
    label(d, 320, 250, "导汽管（铜/竹）", fs=15)
    # 冷凝
    d.rectangle([(370, 120), (640, 220)], fill=(225, 240, 250), outline=(40, 90, 140), width=3)
    label(d, 385, 140, "冷凝桶（ continuously 换冷水）", fs=15)
    d.line([(430, 200), (430, 260), (560, 260), (560, 215)], fill=(80, 80, 80), width=5)
    label(d, 450, 268, "蛇形冷凝管（浸在冷水中）", fs=15)
    # 接收瓶
    d.polygon([(590, 260), (640, 260), (700, 380), (630, 380)], fill=(245, 250, 245), outline=(60, 60, 60), width=2)
    arrow(d, (566, 235), (600, 275), width=3)
    d.rectangle([(660, 330), (960, 380)], fill=(245, 245, 220), outline=(120, 100, 40), width=2)
    label(d, 670, 345, "接收瓶：上层油状=精油，下层水=花水（纯露）", fs=16)
    label(d, 120, 60, "关键：冷凝水必须够冷（加冰块/井水勤换）；温度过高香气会焦糊；", fs=16)
    label(d, 120, 88, "      整套器具忌用铁器（串味），铜、锡、陶、玻璃最好。", fs=16)
    label(d, 120, 540, "流程：鲜花+清水入锅 → 加热至沸 → 蒸汽带出芳香油 → 冷凝 → 油水分层 → 分液取油", fs=16)
    save(im, "04_蒸馏装置.png")


# 5. 块炼铁炉（bloomery）剖面
def img_bloomery():
    im, d = new(1000, 620, "图4-1  块炼铁炉（矮竖炉）剖面图")
    # 炉体
    d.polygon([(300, 150), (560, 150), (600, 480), (260, 480)], fill=(225, 215, 200), outline=(80, 60, 40), width=3)
    label(d, 320, 170, "炉身：耐火黏土+熟料+砂\n夯筑或泥条盘筑", fs=15)
    # 内膛
    d.polygon([(340, 190), (520, 190), (545, 460), (315, 460)], fill=(60, 40, 30), outline=(30, 20, 10), width=2)
    label(d, 355, 250, "炉膛", fs=16, fill=(240, 200, 150))
    # 装料
    d.rectangle([(350, 300), (510, 360)], fill=(120, 120, 120))
    label(d, 360, 320, "木炭 + 矿石（分层）", fs=15, fill=(255, 255, 255))
    d.rectangle([(350, 380), (510, 450)], fill=(150, 70, 30))
    label(d, 365, 405, "炉缸（积海绵铁）", fs=15, fill=(255, 255, 255))
    # 风口
    d.rectangle([(240, 400), (300, 430)], fill=(200, 200, 200), outline=(60, 60, 60), width=3)
    label(d, 150, 405, "风口\n（陶管）", fs=15)
    arrow(d, (150, 415), (238, 415), color=(180, 40, 40), width=4)
    label(d, 100, 445, "鼓风", fs=17, color=(180, 40, 40))
    # 烟囱/排烟
    d.rectangle([(400, 90), (460, 150)], fill=(240, 240, 240), outline=(80, 80, 80), width=2)
    for i in range(3):
        d.ellipse([(415 + i * 6, 60 - i * 12), (445 + i * 6, 85 - i * 12)], fill=(200, 200, 200))
    label(d, 470, 95, "排烟/加料口", fs=15)
    # 标注
    label(d, 640, 150, "典型尺寸（家用级）：", fs=19)
    for i, t in enumerate(["• 炉高 1.0~1.5 m，内径 30~40 cm", "• 炉缸直径 25 cm，深 25~30 cm",
                           "• 风口 1~2 个，直径 3~4 cm，下倾 10~15°", "• 炉壁厚 8~12 cm（耐火泥夯筑）",
                           "• 炉温需达 1150~1300 ℃", "• 单次产海绵铁 2~5 kg，耗时 2~4 小时"]):
        label(d, 640, 185 + i * 30, t, fs=16)
    label(d, 640, 380, "燃料：硬木炭（栎、柞木最佳），忌用含硫煤", fs=16)
    label(d, 640, 412, "矿石：赤铁矿/磁铁矿，破碎至核桃大小，先焙烧", fs=16)
    label(d, 640, 444, "产物：海绵铁（含渣）→ 趁热锻打挤出渣 → 成块炼铁", fs=16)
    label(d, 300, 520, "※ 一氧化碳剧毒：炉必须露天或强通风，出现头痛恶心立即撤离", fs=17, color=(170, 30, 30))
    save(im, "05_块炼铁炉.png")


# 6. 馒头窑（砖窑）剖面
def img_kiln():
    im, d = new(1000, 600, "图4-2  馒头窑（间歇式砖瓦窑）剖面图")
    # 窑体拱形
    d.polygon([(180, 480), (180, 260), (560, 260), (560, 480)], fill=(230, 220, 205), outline=(90, 70, 50), width=3)
    d.pieslice([(180, 130), (560, 390)], 180, 360, fill=(230, 220, 205), outline=(90, 70, 50), width=3)
    d.polygon([(240, 300), (500, 300), (500, 470), (240, 470)], fill=(70, 50, 40), outline=(40, 30, 20), width=2)
    label(d, 260, 320, "窑室（装砖坯）", fs=16, fill=(250, 220, 180))
    # 火膛
    d.rectangle([(180, 430), (240, 470)], fill=(200, 100, 40), outline=(80, 40, 20), width=2)
    label(d, 130, 445, "火膛", fs=16)
    # 烟道与烟囱
    d.rectangle([(300, 250), (340, 300)], fill=(180, 180, 180), outline=(60, 60, 60), width=2)
    label(d, 290, 222, "烟道", fs=15)
    d.rectangle([(430, 60), (490, 260)], fill=(200, 200, 200), outline=(60, 60, 60), width=3)
    label(d, 440, 80, "烟囱", fs=16)
    for i in range(4):
        d.ellipse([(445 + i * 4, 40 - i * 15), (475 + i * 4, 62 - i * 15)], fill=(190, 190, 190))
    # 窑门
    d.rectangle([(500, 380), (560, 470)], fill=(160, 140, 120), outline=(60, 60, 60), width=2)
    label(d, 570, 415, "窑门（装出窑用，\n烧时封闭）", fs=15)
    # 砖坯
    for r in range(4):
        for c in range(6):
            x = 255 + c * 40
            y = 340 + r * 30
            d.rectangle([(x, y), (x + 34, y + 24)], fill=(190, 120, 80), outline=(120, 70, 40), width=1)
    label(d, 620, 150, "烧成曲线（柴烧，全程约 60~90 小时）：", fs=19)
    curve = [("① 小火脱水", "100~200℃ 排干坯体水，约 12~24 h"),
             ("② 升温氧化", "200~600℃ 缓慢升温，约 12 h"),
             ("③ 大火烧成", "600~950~1100℃ 保温 8~20 h"),
             ("④ 保温匀火", "停火前 2~4 h 减小抽力，均热"),
             ("⑤ 冷却", "封窑自然冷却 2~3 天，急冷会裂")]
    for i, (a, b) in enumerate(curve):
        label(d, 620, 190 + i * 46, a, fs=17, color=(150, 60, 20))
        label(d, 620, 214 + i * 46, b, fs=15)
    label(d, 620, 440, "看火色判温（经验值）：", fs=18)
    for i, t in enumerate(["暗红 600℃ ｜ 樱桃红 800℃", "橙黄 1000℃ ｜ 亮黄白 1200~1300℃"]):
        label(d, 620, 472 + i * 28, t, fs=16)
    label(d, 180, 520, "※ 砖坯必须阴干 7~15 天再入窑；窑基须高于地下水位、四周设排水沟", fs=17, color=(150, 60, 20))
    save(im, "06_砖窑剖面.png")


# 7. 充电系统
def img_charging():
    im, d = new(1000, 580, "图5-1  古代给手机充电：从人力到 USB 的完整链路")
    blocks = [("人力/水力\n（脚踏·手摇·水车）", (255, 240, 220)),
              ("发电机\n（永磁+线圈）", (230, 240, 255)),
              ("整流\n（氧化亚铜/机械换向）", (240, 255, 240)),
              ("储能\n（自制铅酸电池 6V）", (255, 235, 235)),
              ("稳压与限流\n（分压+手动调节）", (245, 240, 255)),
              ("USB 口\n（D+D-短接/CC下拉）", (235, 250, 245)),
              ("手机", (255, 255, 220))]
    x, y, bw, bh = 40, 110, 128, 100
    for i, (t, col) in enumerate(blocks):
        bx = x + i * (bw + 8)
        box(d, bx, y, bw, bh, t, fill=col, outline=(60, 60, 60), fs=15)
        if i < len(blocks) - 1:
            arrow(d, (bx + bw + 2, y + bh / 2), (bx + bw + 6, y + bh / 2))
    label(d, 40, 240, "各环节要点：", fs=19)
    notes = [
        "① 人力：成年人持续输出 50~80 W（短时 150 W），摇 30 分钟≈25 Wh，够充满一部手机。",
        "② 发电机：有现代小马达（直流有刷）最好；无则绕线圈+磁铁自制，转速越高电压越高。",
        "③ 整流：无二极管时代用氧化亚铜整流片（铜片高温氧化）或机械换向器（铜环+电刷）。",
        "④ 储能：铅酸电池最实用（铅板+稀硫酸），可反复充放，还能稳压缓冲。硫酸可用干馏绿矾法制取。",
        "⑤ 稳压：手机要 5V±5%。最稳做法：先把铅酸电池充到 6.3V，再用分压/串联灯丝限流降至 5.0~5.2V，",
        "     并串一只电流表（自制磁针式）监测，电压一高立即减摇或并接负载。",
        "⑥ 接口识别：USB-A 口把 D+ 与 D- 短接（或各接 200Ω 再并）→ 手机识别为专用充电口取 1A 以上；",
        "     Type-C 口必须在 CC1/CC2 各接 5.1kΩ 到 GND，否则手机不取电。",
    ]
    for i, t in enumerate(notes):
        label(d, 40, 275 + i * 33, t, fs=15)
    save(im, "07_充电系统.png")


# 8. 电池结构
def img_battery():
    im, d = new(1000, 520, "图6-1  三种可自制的化学电源")
    # 伏打电池
    label(d, 60, 80, "① 伏打电池（最易做，一次性）", fs=19, color=(150, 60, 20))
    for i in range(4):
        y = 130 + i * 46
        d.rectangle([(70, y), (240, y + 22)], fill=(200, 200, 200), outline=(60, 60, 60), width=2)
        label(d, 80, y + 3, "锌片（或锌皮）", fs=14)
        d.rectangle([(70, y + 24), (240, y + 44)], fill=(230, 220, 200), outline=(60, 60, 60), width=2)
        label(d, 80, y + 26, "盐水浸透的布/纸", fs=14)
        d.rectangle([(70, y + 46), (240, y + 66)], fill=(200, 130, 60), outline=(60, 60, 60), width=2)
        label(d, 80, y + 48, "铜片", fs=14)
    label(d, 260, 150, "每单元 ≈ 0.8~1.0 V", fs=17)
    label(d, 260, 182, "串联 6 节 ≈ 5 V", fs=17)
    label(d, 260, 214, "缺点：极化快，", fs=15)
    label(d, 260, 238, "只能小电流短时放电", fs=15)
    # 丹尼尔
    label(d, 400, 80, "② 丹尼尔电池（电压稳定）", fs=19, color=(150, 60, 20))
    d.rectangle([(400, 130), (640, 330)], fill=(240, 248, 255), outline=(60, 60, 60), width=3)
    d.line([(520, 130), (520, 300)], fill=(60, 60, 60), width=3)
    label(d, 415, 150, "锌棒\n硫酸锌溶液", fs=15)
    label(d, 545, 150, "铜棒\n硫酸铜溶液", fs=15)
    label(d, 415, 230, "多孔陶罐/\n盐桥连通", fs=14)
    label(d, 400, 350, "每单元 ≈ 1.1 V，放电平稳", fs=16)
    label(d, 400, 378, "需硫酸铜（胆矾，易得）", fs=15)
    # 铅酸
    label(d, 700, 80, "③ 铅酸电池（可充电，最有用）", fs=19, color=(150, 60, 20))
    d.rectangle([(700, 130), (940, 330)], fill=(245, 245, 235), outline=(60, 60, 60), width=3)
    d.rectangle([(730, 160), (760, 300)], fill=(120, 120, 130), outline=(40, 40, 40), width=2)
    d.rectangle([(800, 160), (830, 300)], fill=(150, 90, 60), outline=(40, 40, 40), width=2)
    d.rectangle([(870, 160), (900, 300)], fill=(120, 120, 130), outline=(40, 40, 40), width=2)
    label(d, 720, 340, "Pb ｜ 稀硫酸(约30%) ｜ PbO₂", fs=15)
    label(d, 700, 378, "单格 2.0 V，三格串联 = 6 V", fs=16)
    label(d, 700, 406, "可反复充放电数百次", fs=15)
    label(d, 700, 434, "硫酸来源：干馏绿矾（硫酸亚铁）", fs=15)
    label(d, 700, 462, "→ 冷凝得稀硫酸，陶器蒸发浓缩", fs=15)
    label(d, 60, 470, "提示：电池串联提高电压、并联提高容量；接线前用磁针电流计确认极性；硫酸操作必须戴手套护眼。", fs=15, color=(170, 30, 30))
    save(im, "08_自制电池.png")


# 9. 手摇发电机结构
def img_generator():
    im, d = new(1000, 520, "图6-2  手摇发电机结构示意（无现代马达时的自制方案）")
    # 曲柄
    d.line([(120, 260), (200, 260)], fill=(60, 60, 60), width=6)
    d.line([(200, 260), (200, 200)], fill=(60, 60, 60), width=6)
    d.ellipse([(190, 180), (215, 205)], fill=(200, 180, 140), outline=(60, 60, 60), width=2)
    label(d, 100, 275, "摇柄", fs=16)
    # 大轮增速
    d.ellipse([(230, 180), (350, 300)], outline=(80, 80, 80), width=4)
    d.ellipse([(370, 220), (430, 280)], outline=(80, 80, 80), width=4)
    d.line([(350, 240), (370, 250)], fill=(80, 80, 80), width=6)
    label(d, 235, 310, "大轮（增速 1:5~1:10）", fs=15)
    label(d, 375, 290, "小轮", fs=15)
    # 转子磁铁
    d.line([(430, 250), (520, 250)], fill=(60, 60, 60), width=5)
    d.rectangle([(520, 200), (600, 300)], fill=(230, 240, 255), outline=(40, 70, 110), width=3)
    label(d, 530, 220, "转子：磁铁\n（N/S 交替）", fs=15)
    # 定子线圈
    d.rectangle([(620, 180), (720, 320)], fill=(255, 240, 220), outline=(150, 100, 40), width=3)
    label(d, 630, 200, "定子：线圈\n（漆包线/丝包线）", fs=15)
    # 输出
    d.line([(720, 250), (800, 250)], fill=(60, 60, 60), width=5)
    d.rectangle([(800, 215), (900, 285)], fill=(240, 255, 240), outline=(40, 120, 60), width=3)
    label(d, 810, 240, "换向器+电刷\n输出直流", fs=14)
    label(d, 120, 60, "要点：", fs=19)
    for i, t in enumerate([
        "• 电压估算：U ≈ 4.44 × f × N × Φ（工频类公式，手摇时 f=转速/60×极对数）",
        "  实用做法：先绕 300~500 匝试转，用磁针电流计测偏转，匝数不够就加绕。",
        "• 磁铁：天然磁石太弱；优先拆现代物件（耳机、喇叭、门吸、包扣、马达磁钢）。",
        "• 无磁铁替代：用电池给电磁铁励磁（自励发电机），先起振后自维持。",
        "• 导线绝缘：漆包线最优；无则用丝线缠绕（丝包线）或生漆（大漆）涂覆烘干。",
        "• 换向器：铜片圆环分段 + 炭刷（石墨可用炭棒/铜辫），把交流变脉动直流。",
    ]):
        label(d, 120, 340 + i * 28, t if i == 0 else t, fs=15)
    save(im, "09_发电机结构.png")


if __name__ == "__main__":
    img_penicillin()
    img_filter()
    img_lye()
    img_distill()
    img_bloomery()
    img_kiln()
    img_charging()
    img_battery()
    img_generator()
    print("ALL IMAGES DONE")
