from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

def generate_market_card(match_context) -> bytes:
    """
    Gera um card visual (Dark Theme) com as métricas do jogo para Telegram.
    Retorna os bytes da imagem PNG.
    """
    # Configurações de cores e dimensões
    WIDTH, HEIGHT = 800, 400
    BG_COLOR = (18, 18, 20)      # #121214
    TEXT_MAIN = (240, 244, 248)  # #F0F4F8
    TEXT_MUTED = (139, 155, 180) # #8B9BB4
    NEON_GREEN = (0, 230, 118)   # #00E676
    NEON_BLUE = (0, 229, 255)    # #00E5FF
    BAR_BG = (40, 40, 45)
    
    metrics = match_context.live_metrics
    
    # Cria a imagem
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Tenta carregar uma fonte padrao (se falhar usa a default do Pillow)
    try:
        font_lg = ImageFont.truetype("arial.ttf", 36)
        font_md = ImageFont.truetype("arial.ttf", 24)
        font_sm = ImageFont.truetype("arial.ttf", 18)
        font_bold = ImageFont.truetype("arialbd.ttf", 28)
    except:
        font_lg = font_md = font_sm = font_bold = ImageFont.load_default()
        
    # Draw Watermark (Background pattern)
    try:
        watermark = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
        w_draw = ImageDraw.Draw(watermark)
        for i in range(-200, 1000, 100):
            w_draw.line([(i, 0), (i+400, HEIGHT)], fill=(255, 255, 255, 5), width=2)
        img.paste(watermark, mask=watermark)
    except:
        pass
        
    # HEADER
    draw.text((30, 20), "MARKET MONITOR PRO", font=font_sm, fill=NEON_BLUE)
    draw.text((WIDTH - 120, 20), f"{metrics.match_time}' MIN", font=font_bold, fill=NEON_GREEN)
    
    # Teams & Score
    home = match_context.home_team.team_name[:20].upper()
    away = match_context.away_team.team_name[:20].upper()
    score = f"{metrics.current_score[0]} - {metrics.current_score[1]}"
    
    draw.text((30, 70), f"{home} vs {away}", font=font_bold, fill=TEXT_MAIN)
    draw.text((30, 110), score, font=font_lg, fill=NEON_BLUE)
    
    # Competition
    comp = match_context.competition[:40]
    draw.text((30, 160), comp, font=font_sm, fill=TEXT_MUTED)
    
    # Divider
    draw.line([(30, 190), (WIDTH - 30, 190)], fill=(255,255,255,30), width=1)
    
    # METRICS SECTION
    def draw_progress_bar(x, y, w, h, label, value, max_val, color):
        # Draw label & value
        draw.text((x, y), label, font=font_sm, fill=TEXT_MUTED)
        draw.text((x + w - 40, y), str(value), font=font_bold, fill=color)
        # Background bar
        bar_y = y + 30
        draw.rounded_rectangle([x, bar_y, x+w, bar_y+h], radius=4, fill=BAR_BG)
        # Fill bar
        fill_w = min(int((value / max_val) * w), w)
        if fill_w > 0:
            draw.rounded_rectangle([x, bar_y, x+fill_w, bar_y+h], radius=4, fill=color)
            
    # Attacks (Max ~80)
    attacks = metrics.dangerous_attacks
    draw_progress_bar(30, 220, 340, 12, "ATAQUES PERIGOSOS", attacks, 80, NEON_GREEN)
    
    # APM (Attacks per minute)
    apm = round(attacks / max(metrics.match_time, 1), 2)
    draw_progress_bar(420, 220, 340, 12, "PRESSÃO (APM)", apm, 2.0, (255, 170, 0) if apm >= 1.0 else NEON_BLUE)
    
    # Shots on Target (Max ~10)
    shots = metrics.shots_on_target
    draw_progress_bar(30, 300, 340, 12, "CHUTES NO GOL", shots, 10, NEON_GREEN)
    
    # xG or Fair Odd
    if metrics.xg_home is not None:
        xg_tot = round(metrics.xg_home + (metrics.xg_away or 0), 2)
        draw_progress_bar(420, 300, 340, 12, "EXPECTED GOALS (xG)", xg_tot, 2.5, NEON_BLUE)
    else:
        corners = metrics.corners
        draw_progress_bar(420, 300, 340, 12, "ESCANTEIOS", corners, 10, NEON_BLUE)
        
    # Converter para bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
