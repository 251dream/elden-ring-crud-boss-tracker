from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'elden-ring-2026' # app secret
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bosses.db' # db path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True # track mods
db = SQLAlchemy(app)

# boss table model
class Boss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    map_x = db.Column(db.Float, default=50.0)
    map_y = db.Column(db.Float, default=50.0)
    defeated = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=1)
    difficulty_rating = db.Column(db.Integer, default=5)
    player_notes = db.Column(db.Text, default='')
    reward = db.Column(db.String(300), default='')
    first_encounter_date = db.Column(db.Date, default=date.today)
    defeated_date = db.Column(db.Date, nullable=True)
    boss_type = db.Column(db.String(80), default='Field Boss')
    image_url = db.Column(db.String(500), default='')
    randomizer_slot = db.Column(db.String(120), default='')
    is_randomized = db.Column(db.Boolean, default=False)
    is_mandatory = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=999)

    def status(self):
        if self.defeated:
            return 'defeated' # done
        if self.attempts > 1:
            return 'progress' # in progress
        return 'encountered' # seen

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'map_x': self.map_x,
            'map_y': self.map_y,
            'defeated': self.defeated,
            'attempts': self.attempts,
            'difficulty_rating': self.difficulty_rating,
            'player_notes': self.player_notes,
            'reward': self.reward,
            'first_encounter_date': str(self.first_encounter_date) if self.first_encounter_date else None,
            'defeated_date': str(self.defeated_date) if self.defeated_date else None,
            'boss_type': self.boss_type,
            'image_url': self.image_url,
            'randomizer_slot': self.randomizer_slot,
            'is_randomized': self.is_randomized,
            'is_mandatory': self.is_mandatory,
            'display_order': self.display_order,
            'status': self.status(),
        }

# mandatory bosses data
MANDATORY_BOSSES = [
    {'order': 1,  'name': 'Soldier of God, Rick',
     'region': 'Limgrave', 'map_x': 38.5, 'map_y': 80.1,
     'boss_type': 'Shardbearer Guardian', 'difficulty_rating': 10,
     'reward': 'Aura',
     'image_url': '/static/images/bosses/soldierofgod_rick.jpg'},
    {'order': 2,  'name': 'Margit, the Fell Omen',
     'region': 'Limgrave', 'map_x': 34.0, 'map_y': 74.1,
     'boss_type': 'Shardbearer Guardian', 'difficulty_rating': 5,
     'reward': 'Talisman Pouch',
     'image_url': '/static/images/bosses/margit.jpg'},
    {'order': 3,  'name': 'Godrick the Grafted',
     'region': 'Stormveil Castle', 'map_x': 31.8, 'map_y': 70.1,
     'boss_type': 'Shardbearer', 'difficulty_rating': 6,
     'reward': "Godrick's Great Rune, Remembrance of the Grafted",
     'image_url': '/static/images/bosses/godrick.jpg'},
    {'order': 4,  'name': 'Red Wolf of Radagon',
     'region': 'Academy of Raya Lucaria', 'map_x': 20.1, 'map_y': 54.5,
     'boss_type': 'Field Boss', 'difficulty_rating': 6,
     'reward': 'Memory Stone',
     'image_url': '/static/images/bosses/red_wolf.jpg'},
    {'order': 5,  'name': 'Rennala, Queen of the Full Moon',
     'region': 'Academy of Raya Lucaria', 'map_x': 19.2, 'map_y': 52.4,
     'boss_type': 'Shardbearer', 'difficulty_rating': 5,
     'reward': 'Great Rune of the Unborn, Remembrance of the Full Moon Queen',
     'image_url': '/static/images/bosses/rennala.jpg'},
    {'order': 6,  'name': 'Godfrey, First Elden Lord (Golden Shade)',
     'region': 'Leyndell, Royal Capital', 'map_x': 44.3, 'map_y': 38.9,
     'boss_type': 'Spectral Boss', 'difficulty_rating': 6,
     'reward': 'Talisman Pouch',
     'image_url': '/static/images/bosses/godfrey_gold.jpg'},
    {'order': 7,  'name': 'Morgott, the Omen King',
     'region': 'Leyndell, Royal Capital', 'map_x': 46.0, 'map_y': 39.8,
     'boss_type': 'Shardbearer Guardian', 'difficulty_rating': 8,
     'reward': "Morgott's Great Rune, Remembrance of the Omen King",
     'image_url': '/static/images/bosses/morgott.jpg'},
    {'order': 8,  'name': 'Fire Giant',
     'region': 'Mountaintops of the Giants', 'map_x': 66.3, 'map_y': 33.8,
     'boss_type': 'Demi-God', 'difficulty_rating': 8,
     'reward': 'Remembrance of the Fire Giant',
     'image_url': '/static/images/bosses/fire_giant.jpg'},
    {'order': 9,  'name': 'Godskin Duo',
     'region': 'Crumbling Farum Azula', 'map_x': 87.4, 'map_y': 47.9,
     'boss_type': 'Required Boss', 'difficulty_rating': 8,
     'reward': "Smithing-Stone Miner's Bell Bearing [4]",
     'image_url': '/static/images/bosses/godskin_duo.jpg'},
    {'order': 10,  'name': 'Maliketh, the Black Blade',
     'region': 'Crumbling Farum Azula', 'map_x': 89.3, 'map_y': 48.4,
     'boss_type': "Empyrean's Vassal", 'difficulty_rating': 9,
     'reward': 'Remembrance of the Black Blade, Destined Death',
     'image_url': '/static/images/bosses/maliketh.jpg'},
    {'order': 11, 'name': 'Sir Gideon Ofnir, the All-Knowing',
     'region': 'Leyndell, Ashen Capital', 'map_x': 44.8, 'map_y': 40.2,
     'boss_type': 'Required Boss', 'difficulty_rating': 5,
     'reward': 'All-Knowing Armor Set, Scepter of the All-Knowing',
     'image_url': '/static/images/bosses/gideon.jpg'},
    {'order': 12, 'name': 'Godfrey, First Elden Lord / Hoarah Loux, Warrior',
     'region': 'Leyndell, Ashen Capital', 'map_x': 46.3, 'map_y': 40.3,
     'boss_type': 'Demi-God', 'difficulty_rating': 9,
     'reward': 'Talisman Pouch, Remembrance of Hoarah Loux',
     'image_url': '/static/images/bosses/godfrey2.jpg'},
    {'order': 13, 'name': 'Radagon of the Golden Order',
     'region': 'Erdtree — Elden Throne', 'map_x': 48.0, 'map_y': 42.6,
     'boss_type': 'God', 'difficulty_rating': 9,
     'reward': 'None (leads to Elden Beast)',
     'image_url': '/static/images/bosses/radagon.jpg'},
    {'order': 14, 'name': 'Elden Beast',
     'region': 'Erdtree — Elden Throne', 'map_x': 48.5, 'map_y': 42.6,
     'boss_type': 'Final Boss', 'difficulty_rating': 10,
     'reward': 'Elden Ring — Ending unlocked',
     'image_url': '/static/images/bosses/elden_beast.jpg'},
]

# default location mapping
DEFAULT_LOCATIONS = {
    b['name']: {'region': b['region'], 'map_x': b['map_x'], 'map_y': b['map_y']}
    for b in MANDATORY_BOSSES
}

# map slot presets
ALL_MAP_SLOTS = [
    {'slot': 'Limgrave – Stormhill',   'region': 'Limgrave',                   'map_x': 52.0, 'map_y': 60.5},
    {'slot': 'Stormveil Throne',       'region': 'Stormveil Castle',           'map_x': 47.5, 'map_y': 57.0},
    {'slot': 'Raya Lucaria Library',   'region': 'Academy of Raya Lucaria',    'map_x': 43.5, 'map_y': 45.0},
    {'slot': 'Redmane Castle',         'region': 'Caelid',                     'map_x': 68.5, 'map_y': 58.0},
    {'slot': 'Leyndell Throne',        'region': 'Leyndell, Royal Capital',    'map_x': 56.0, 'map_y': 50.5},
    {'slot': 'Haligtree Roots',        'region': 'Haligtree',                  'map_x': 28.5, 'map_y': 20.0},
    {'slot': 'Giants Mountaintop',     'region': 'Mountaintops of the Giants', 'map_x': 72.0, 'map_y': 30.0},
    {'slot': 'Farum Azula Apex',       'region': 'Crumbling Farum Azula',      'map_x': 80.0, 'map_y': 38.0},
    {'slot': 'Elden Throne',           'region': 'Erdtree — Elden Throne',     'map_x': 56.5, 'map_y': 49.5},
    {'slot': 'Volcano Manor',          'region': 'Mt. Gelmir',                 'map_x': 32.0, 'map_y': 42.0},
]

# seed db with bosses
def seed_database():
    if Boss.query.count() == 0:
        for b in MANDATORY_BOSSES:
            boss = Boss(
                name=b['name'],
                region=b['region'],
                map_x=b['map_x'],
                map_y=b['map_y'],
                defeated=False,
                attempts=1,
                difficulty_rating=b['difficulty_rating'],
                player_notes='',
                reward=b['reward'],
                first_encounter_date=date.today(),
                boss_type=b['boss_type'],
                image_url=b['image_url'],
                is_mandatory=True,
                display_order=b['order'],
            )
            db.session.add(boss)
        db.session.commit()
        print(f"Seeded {len(MANDATORY_BOSSES)} bosses.")

# clean static path
def _normalize_static_path(rel_path):
    clean = (rel_path or '').strip()
    clean = clean.replace('\\', '/')

    if clean.startswith('/static/'):
        clean = clean[len('/static/'):]
    elif clean.startswith('static/'):
        clean = clean[len('static/'):]

    clean = clean.lstrip('/').strip()
    return clean

# possible static dirs
def _candidate_static_roots():
    roots = []

    if app.static_folder:
        roots.append(app.static_folder)

    roots.append(os.path.join(app.root_path, 'static'))
    roots.append(os.path.join(os.getcwd(), 'static'))
    roots.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

    uniq = []
    for r in roots:
        if r and r not in uniq:
            uniq.append(r)
    return uniq

# resolve static file
def _resolve_static_file(rel_path):
    clean = _normalize_static_path(rel_path)
    if not clean:
        return None

    for root in _candidate_static_roots():
        full = os.path.abspath(os.path.join(root, clean))
        if os.path.exists(full) and os.path.isfile(full):
            return full

    return None

# read image as base64
def _read_static_as_b64(rel_path):
    import os
    import base64

    clean = (rel_path or '').strip().replace('\\', '/')
    if clean.startswith('/static/'):
        clean = clean[len('/static/'):]
    elif clean.startswith('static/'):
        clean = clean[len('static/'):]

    full = os.path.join(app.static_folder, clean)

    print('[export] requested =', rel_path)
    print('[export] resolved =', full)
    print('[export] exists =', os.path.exists(full))

    if not os.path.exists(full) or not os.path.isfile(full):
        return ''

    ext = os.path.splitext(full)[1].lower()
    mime = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }.get(ext, 'application/octet-stream')

    with open(full, 'rb') as f:
        data = base64.b64encode(f.read()).decode('ascii')

    return f'data:{mime};base64,{data}'

@app.route('/')
def index():
    bosses = Boss.query.order_by(Boss.display_order.asc(), Boss.name.asc()).all()
    total = len(bosses)
    defeated = sum(1 for b in bosses if b.defeated)
    avg_diff = round(sum(b.difficulty_rating for b in bosses) / total, 1) if total else 0
    total_att = sum(b.attempts for b in bosses)

    return render_template(
        'index.html',
        bosses=bosses,
        total=total,
        defeated=defeated,
        undefeated=total - defeated,
        avg_diff=avg_diff,
        total_attempts=total_att,
        map_slots=ALL_MAP_SLOTS
    )

# list bosses
@app.route('/bosses')
def boss_list():
    search = request.args.get('search', '').strip()
    region_f = request.args.get('region', '')
    status_f = request.args.get('status', '')
    sort_by = request.args.get('sort', 'order')

    q = Boss.query

    if search:
        q = q.filter(Boss.name.ilike(f'%{search}%'))
    if region_f:
        q = q.filter(Boss.region == region_f)
    if status_f == 'defeated':
        q = q.filter(Boss.defeated == True)
    elif status_f == 'undefeated':
        q = q.filter(Boss.defeated == False)

    if sort_by == 'difficulty':
        q = q.order_by(Boss.difficulty_rating.desc())
    elif sort_by == 'attempts':
        q = q.order_by(Boss.attempts.desc())
    elif sort_by == 'date':
        q = q.order_by(Boss.first_encounter_date.asc())
    elif sort_by == 'name':
        q = q.order_by(Boss.name.asc())
    else:
        q = q.order_by(Boss.display_order.asc(), Boss.name.asc())

    bosses = q.all()
    regions = sorted(set(b.region for b in Boss.query.all()))

    return render_template(
        'boss_list.html',
        bosses=bosses,
        regions=regions,
        search=search,
        region_filter=region_f,
        status_filter=status_f,
        sort_by=sort_by
    )


@app.route('/boss/<int:boss_id>')
def boss_detail(boss_id):
    boss = Boss.query.get_or_404(boss_id)
    return render_template('boss_detail.html', boss=boss, map_slots=ALL_MAP_SLOTS)


@app.route('/boss/add', methods=['GET', 'POST'])
def add_boss():
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            is_rand = 'is_randomized' in request.form
            rand_slot = request.form.get('randomizer_slot', '').strip()

            if not is_rand and name in DEFAULT_LOCATIONS:
                loc = DEFAULT_LOCATIONS[name]
                map_x = float(request.form.get('map_x', loc['map_x']))
                map_y = float(request.form.get('map_y', loc['map_y']))
                region = request.form.get('region', '').strip() or loc['region']
            else:
                map_x = float(request.form.get('map_x', 50))
                map_y = float(request.form.get('map_y', 50))
                region = request.form.get('region', '').strip()

            if is_rand and rand_slot:
                slot = next((s for s in ALL_MAP_SLOTS if s['slot'] == rand_slot), None)
                if slot:
                    map_x = slot['map_x']
                    map_y = slot['map_y']
                    region = slot['region']

            defeated = 'defeated' in request.form
            d_date = None
            if request.form.get('defeated_date'):
                d_date = datetime.strptime(request.form['defeated_date'], '%Y-%m-%d').date()

            f_date = date.today()
            if request.form.get('first_encounter_date'):
                f_date = datetime.strptime(request.form['first_encounter_date'], '%Y-%m-%d').date()

            boss = Boss(
                name=name,
                region=region,
                map_x=map_x,
                map_y=map_y,
                defeated=defeated,
                attempts=max(1, int(request.form.get('attempts', 1))),
                difficulty_rating=max(1, min(10, int(request.form.get('difficulty_rating', 5)))),
                player_notes=request.form.get('player_notes', '').strip(),
                reward=request.form.get('reward', '').strip(),
                first_encounter_date=f_date,
                defeated_date=d_date,
                boss_type=request.form.get('boss_type', 'Field Boss').strip(),
                image_url=request.form.get('image_url', '').strip(),
                is_randomized=is_rand,
                randomizer_slot=rand_slot,
                is_mandatory=False,
                display_order=999,
            )

            db.session.add(boss)
            db.session.commit()
            flash(f'"{boss.name}" added.', 'success')
            return redirect(url_for('boss_list'))

        except Exception as e:
            flash(f'Error: {e}', 'error')

    return render_template(
        'add_boss.html',
        map_slots=ALL_MAP_SLOTS,
        default_locations=DEFAULT_LOCATIONS,
        mandatory_names=[b['name'] for b in MANDATORY_BOSSES],
        prefill_name=request.args.get('name', ''),
        prefill_slot=request.args.get('slot', '')
    )


@app.route('/boss/edit/<int:boss_id>', methods=['GET', 'POST'])
def edit_boss(boss_id):
    boss = Boss.query.get_or_404(boss_id)

    if request.method == 'POST':
        try:
            boss.name = request.form['name'].strip()
            boss.region = request.form['region'].strip()
            boss.map_x = float(request.form.get('map_x', 50))
            boss.map_y = float(request.form.get('map_y', 50))
            boss.defeated = 'defeated' in request.form
            boss.attempts = max(1, int(request.form.get('attempts', 1)))
            boss.difficulty_rating = max(1, min(10, int(request.form.get('difficulty_rating', 5))))
            boss.player_notes = request.form.get('player_notes', '').strip()
            boss.reward = request.form.get('reward', '').strip()
            boss.boss_type = request.form.get('boss_type', 'Field Boss').strip()
            boss.image_url = request.form.get('image_url', '').strip()
            boss.is_randomized = 'is_randomized' in request.form
            boss.randomizer_slot = request.form.get('randomizer_slot', '').strip()

            if request.form.get('first_encounter_date'):
                boss.first_encounter_date = datetime.strptime(
                    request.form['first_encounter_date'],
                    '%Y-%m-%d'
                ).date()

            boss.defeated_date = None
            if request.form.get('defeated_date'):
                boss.defeated_date = datetime.strptime(
                    request.form['defeated_date'],
                    '%Y-%m-%d'
                ).date()

            db.session.commit()
            flash(f'"{boss.name}" updated.', 'success')
            return redirect(url_for('boss_detail', boss_id=boss.id))

        except Exception as e:
            flash(f'Error: {e}', 'error')

    return render_template('edit_boss.html', boss=boss, map_slots=ALL_MAP_SLOTS)


@app.route('/boss/delete/<int:boss_id>', methods=['POST'])
def delete_boss(boss_id):
    boss = Boss.query.get_or_404(boss_id)
    name = boss.name
    db.session.delete(boss)
    db.session.commit()
    flash(f'"{name}" removed.', 'success')
    return redirect(url_for('boss_list'))


@app.route('/boss/quick-update/<int:boss_id>', methods=['POST'])
def quick_update(boss_id):
    boss = Boss.query.get_or_404(boss_id)
    action = request.form.get('action')

    if action == 'toggle_defeated':
        boss.defeated = not boss.defeated
        if boss.defeated and not boss.defeated_date:
            boss.defeated_date = date.today()
        elif not boss.defeated:
            boss.defeated_date = None
    elif action == 'increment_attempts':
        boss.attempts += 1

    db.session.commit()
    return redirect(request.referrer or url_for('boss_list'))


@app.route('/api/bosses')
def api_bosses():
    bosses = Boss.query.order_by(Boss.display_order.asc(), Boss.name.asc()).all()
    return jsonify([b.to_dict() for b in bosses])


@app.route('/api/boss/<int:boss_id>')
def api_boss(boss_id):
    return jsonify(Boss.query.get_or_404(boss_id).to_dict())


@app.route('/api/export-data')
def api_export_data():
    bosses = Boss.query.order_by(Boss.display_order.asc(), Boss.name.asc()).all()
    total = len(bosses)
    defeated = sum(1 for b in bosses if b.defeated)
    total_att = sum(b.attempts for b in bosses)
    avg_diff = round(sum(b.difficulty_rating for b in bosses) / total, 1) if total else 0

    boss_list = []
    for b in bosses:
        d = b.to_dict()
        if b.image_url and b.image_url.startswith('/static/'):
            d['image_b64'] = _read_static_as_b64(b.image_url)
        else:
            d['image_b64'] = ''
        boss_list.append(d)

    map_b64 = ''
    map_candidates = [
        '/static/images/map/ER_MAP.jpeg',
    ]

    found_map = None
    for candidate in map_candidates:
        resolved = _resolve_static_file(candidate)
        if resolved:
            found_map = resolved
            map_b64 = _read_static_as_b64(candidate)
            break

    print('[export] app.root_path =', app.root_path)
    print('[export] app.static_folder =', app.static_folder)
    print('[export] cwd =', os.getcwd())
    print('[export] static roots =', _candidate_static_roots())
    print('[export] found map =', found_map)
    print('[export] map_b64 exists =', bool(map_b64))
    print('[export] first boss image exists =', bool(boss_list[0]['image_b64']) if boss_list else False)

    return jsonify({
        'stats': {
            'total': total,
            'defeated': defeated,
            'remaining': total - defeated,
            'avg_difficulty': avg_diff,
            'total_attempts': total_att
        },
        'bosses': boss_list,
        'map_b64': map_b64,
    })


@app.route('/api/image-b64')
def api_image_b64():
    path = request.args.get('path', '')
    if not path.startswith('/static/') or '..' in path:
        return jsonify({'error': 'invalid path'}), 400

    b64 = _read_static_as_b64(path)
    return jsonify({'data': b64})


@app.route('/debug/static-check')
def debug_static_check():
    checks = {
        'app_root_path': app.root_path,
        'app_static_folder': app.static_folder,
        'cwd': os.getcwd(),
        'static_roots': _candidate_static_roots(),
        'map_jpeg': _resolve_static_file('/static/images/map/ER_MAP.jpeg'),
    }
    return jsonify(checks)


@app.route('/seed')
def seed_route():
    seed_database()
    flash('Database seeded with 13 mandatory bosses!', 'success')
    return redirect(url_for('index'))


@app.route('/migrate')
def migrate_db():
    import sqlite3

    db_path = os.path.join(app.instance_path, 'bosses.db')
    if not os.path.exists(db_path):
        flash('No database found.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect(db_path)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(boss)").fetchall()]

        if 'weakness_notes' in cols and 'player_notes' not in cols:
            conn.execute("ALTER TABLE boss ADD COLUMN player_notes TEXT DEFAULT ''")
            conn.execute("UPDATE boss SET player_notes = weakness_notes")
            conn.commit()
            flash('Migrated weakness_notes to player_notes.', 'success')
        elif 'player_notes' not in cols:
            conn.execute("ALTER TABLE boss ADD COLUMN player_notes TEXT DEFAULT ''")
            conn.commit()
            flash('Added player_notes column.', 'success')
        else:
            flash('Database already up to date.', 'success')

        conn.close()

    except Exception as e:
        flash(f'Migration error: {e}', 'error')

    return redirect(url_for('index'))


@app.route('/debug/static-check', endpoint='debug_static_check_v2')
def debug_static_check_v2():
    import os

    def exists(p):
        return {
            'path': p,
            'exists': os.path.exists(p),
            'is_file': os.path.isfile(p)
        }

    root = app.root_path
    static_root = app.static_folder

    checks = {
        'app_root_path': root,
        'app_static_folder': static_root,
        'cwd': os.getcwd(),
        'map_jpeg': exists(os.path.join(static_root, 'images', 'map', 'ER_MAP.jpeg')),
        'margit_jpg': exists(os.path.join(static_root, 'images', 'bosses', 'margit.jpg')),
        'godrick_jpg': exists(os.path.join(static_root, 'images', 'bosses', 'godrick.jpg')),
    }
    return jsonify(checks)


@app.route('/debug/routes')
def debug_routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))




if __name__ == '__main__':
    with app.app_context():
        db.create_all() # create tables
        seed_database() # seed data

    app.run(debug=True) # run app