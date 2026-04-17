from flask import Flask, render_template, jsonify
import random
import json

app = Flask(__name__)

# ============================================================
# ✏️ ここを編集しよう！ （⭐ Lv.1 課題）
# ============================================================

THEME = "食べ物"  # ← テーマ名を変えよう

WORDS_AND_HINTS = [
    {"word": "ラーメン",  "hint": "中華麺を使った日本の国民食"},
    {"word": "カレー",    "hint": "スパイスが効いたごはんのお供"},
    {"word": "テンプラ",  "hint": "衣をつけて油で揚げた料理"},
    {"word": "メロン",    "hint": "高級フルーツの代名詞"},
    {"word": "ネギ",      "hint": "ラーメンのトッピングでおなじみ"},
    {"word": "カニ",      "hint": "横歩きする海の幸"},
    {"word": "ラムネ",    "hint": "夏祭りで飲むビー玉入り飲み物"},
]

# ============================================================
# ⚙️ グリッドサイズ（⭐⭐ Lv.2 課題：数字を変えてみよう）
# ============================================================

GRID_SIZE = 20  # 15〜25がおすすめ

# ============================================================
# 🔧 配置ロジック（ここはいじらなくてOK）
# ============================================================

def create_empty_grid():
    return [['　' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def can_place(grid, word, row, col, direction):
    if direction == 'across':
        if col < 0 or col + len(word) > GRID_SIZE or row < 0 or row >= GRID_SIZE: return False
        if col > 0 and grid[row][col-1] != '　': return False
        if col + len(word) < GRID_SIZE and grid[row][col+len(word)] != '　': return False
        crosses = 0
        for i, char in enumerate(word):
            cell = grid[row][col+i]
            if cell != '　' and cell != char: return False
            if cell == char: crosses += 1
            else:
                if row > 0 and grid[row-1][col+i] != '　': return False
                if row < GRID_SIZE-1 and grid[row+1][col+i] != '　': return False
        return crosses >= 1
    else:
        if row < 0 or row + len(word) > GRID_SIZE or col < 0 or col >= GRID_SIZE: return False
        if row > 0 and grid[row-1][col] != '　': return False
        if row + len(word) < GRID_SIZE and grid[row+len(word)][col] != '　': return False
        crosses = 0
        for i, char in enumerate(word):
            cell = grid[row+i][col]
            if cell != '　' and cell != char: return False
            if cell == char: crosses += 1
            else:
                if col > 0 and grid[row+i][col-1] != '　': return False
                if col < GRID_SIZE-1 and grid[row+i][col+1] != '　': return False
        return crosses >= 1

def place_word(grid, word, row, col, direction):
    for i, char in enumerate(word):
        if direction == 'across': grid[row][col+i] = char
        else: grid[row+i][col] = char

def try_build(words_and_hints, order):
    placed_words = []
    grid = create_empty_grid()
    words = [words_and_hints[i] for i in order]
    word = words[0]['word']
    row = GRID_SIZE // 2
    col = (GRID_SIZE - len(word)) // 2
    place_word(grid, word, row, col, 'across')
    placed_words.append({**words[0], 'row': row, 'col': col, 'direction': 'across'})
    for item in words[1:]:
        word = item['word']
        best = None; best_score = -1
        for placed in placed_words:
            for pi, pchar in enumerate(placed['word']):
                for wi, wchar in enumerate(word):
                    if pchar != wchar: continue
                    new_dir = 'down' if placed['direction'] == 'across' else 'across'
                    if placed['direction'] == 'across':
                        r = placed['row'] - wi; c = placed['col'] + pi
                    else:
                        r = placed['row'] + pi; c = placed['col'] - wi
                    if can_place(grid, word, r, c, new_dir):
                        crosses = sum(1 for i, ch in enumerate(word) if (grid[r][c+i] if new_dir=='across' else grid[r+i][c]) == ch)
                        if crosses > best_score:
                            best_score = crosses; best = (r, c, new_dir)
        if best:
            r, c, d = best
            place_word(grid, word, r, c, d)
            placed_words.append({**item, 'row': r, 'col': c, 'direction': d})
    return grid, placed_words

def build_best_crossword(words_and_hints, trials=300):
    n = len(words_and_hints)
    best_result = None; best_count = 0
    random.seed(42)
    orders = [list(range(n))]
    for _ in range(trials):
        o = list(range(n)); random.shuffle(o); orders.append(o)
    for order in orders:
        grid, placed = try_build(words_and_hints, order)
        if len(placed) > best_count:
            best_count = len(placed); best_result = (grid, placed)
            if best_count == n: break
    return best_result

def prepare_data():
    grid, placed = build_best_crossword(WORDS_AND_HINTS)
    rows_used, cols_used = [], []
    for p in placed:
        if p['direction'] == 'across':
            rows_used.append(p['row'])
            cols_used += list(range(p['col'], p['col'] + len(p['word'])))
        else:
            rows_used += list(range(p['row'], p['row'] + len(p['word'])))
            cols_used.append(p['col'])
    min_r = max(0, min(rows_used) - 1)
    min_c = max(0, min(cols_used) - 1)
    max_r = min(GRID_SIZE - 1, max(rows_used) + 1)
    max_c = min(GRID_SIZE - 1, max(cols_used) + 1)
    trimmed = [grid[r][min_c:max_c+1] for r in range(min_r, max_r+1)]

    num_map = {}
    for i, p in enumerate(sorted(placed, key=lambda p: (p['row'], p['col']))):
        key = (p['row'] - min_r, p['col'] - min_c)
        if key not in num_map:
            num_map[key] = i + 1
        p['num'] = num_map[key]
        p['display_row'] = p['row'] - min_r
        p['display_col'] = p['col'] - min_c

    cells = []
    for r, row in enumerate(trimmed):
        for c, char in enumerate(row):
            if char != '　':
                cells.append({'row': r, 'col': c, 'answer': char, 'num': num_map.get((r, c))})

    skipped = [w['word'] for w in WORDS_AND_HINTS if not any(p['word'] == w['word'] for p in placed)]
    return {
        'rows': len(trimmed),
        'cols': len(trimmed[0]) if trimmed else 0,
        'cells': cells,
        'placed': placed,
        'skipped': skipped,
        'theme': THEME,
        'total': len(WORDS_AND_HINTS),
        'placed_count': len(placed),
    }

@app.route('/')
def index():
    data = prepare_data()
    return render_template('index.html', data=data, data_json=json.dumps(data, ensure_ascii=False))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
