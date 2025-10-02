from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import json
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'sua_chave_secreta_aqui'
DATABASE = 'pontos.db'

# ---------- MATERIAIS ----------
MATERIAL_OPTIONS = {
    "Papel": ["Jornais, revistas e panfletos", "Caixas de papelão", "Papel de escritório", "Embalagens de papel e papelão"],
    "Plástico": ["Garrafas e embalagens plásticas", "Tampas e frascos", "Sacolas plásticas", "Brinquedos de plástico", "Tubos e canos de PVC"],
    "Vidro": ["Garrafa", "Frascos", "Potes"],
    "Metal": ["Latas", "Panelas", "Peças metálicas"],
    "Eletrônicos": ["Celulares", "Baterias", "Cabos e acessórios"],
    "Orgânico": ["Restos de comida", "Resíduos vegetais"]
}

# ---------- BANCO DE DADOS ----------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pontos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                rua TEXT NOT NULL,
                numero TEXT NOT NULL,
                complemento TEXT,
                bairro TEXT NOT NULL,
                cidade TEXT NOT NULL,
                estado TEXT NOT NULL,
                cep TEXT NOT NULL,
                materiais_json TEXT NOT NULL,
                horarios_inicio TEXT NOT NULL,
                horarios_fim TEXT NOT NULL
            )
        ''')
        conn.commit()
    app.logger.info("Banco de dados inicializado ou já existente.")

# ---------- VALIDAÇÃO ----------
def validar_formulario(data):
    required_fields = ['nome','rua','numero','bairro','cidade','estado','cep','horarios_inicio','horarios_fim']
    materiais_presentes = any(data.getlist(key) for key in data if key.startswith('materiais_')) or bool(data.get('materiais_custom','').strip())
    for field in required_fields:
        if not data.get(field):
            return False, f"O campo {field} é obrigatório."
    if not materiais_presentes:
        return False, "Selecione ao menos um tipo de material aceito."
    try:
        datetime.strptime(data['horarios_inicio'], '%H:%M')
        datetime.strptime(data['horarios_fim'], '%H:%M')
    except ValueError:
        return False, "Horários devem estar no formato HH:MM."
    return True, ""

def extrair_materiais(form):
    materiais_dict = {}
    for categoria in MATERIAL_OPTIONS:
        key = f"materiais_{categoria}"
        selecionados = form.getlist(key)
        if selecionados:
            materiais_dict[categoria] = selecionados
    custom_text = form.get('materiais_custom','').strip()
    if custom_text:
        customs = [c.strip() for c in custom_text.split(',') if c.strip()]
        if customs:
            materiais_dict['Custom'] = customs
    return materiais_dict

# ---------- ROTAS ----------
@app.route('/')
def index():
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM pontos ORDER BY nome').fetchall()
    pontos_list = []
    for r in rows:
        d = dict(r)
        try:
            d['materiais'] = json.loads(d.get('materiais_json') or "{}")
        except json.JSONDecodeError:
            d['materiais'] = {}
        pontos_list.append(d)
    return render_template('index.html', pontos=pontos_list)

@app.route('/pontos')
def pontos():
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM pontos ORDER BY nome').fetchall()
    pontos_list = []
    for r in rows:
        d = dict(r)
        try:
            d['materiais'] = json.loads(d.get('materiais_json') or "{}")
        except json.JSONDecodeError:
            d['materiais'] = {}
        pontos_list.append(d)
    success_msg = request.args.get('success')
    return render_template('pontos.html', pontos=pontos_list, success=success_msg, material_options=MATERIAL_OPTIONS)

@app.route('/cadastro', methods=['GET','POST'])
def cadastro():
    if request.method == 'POST':
        valido, msg = validar_formulario(request.form)
        if not valido:
            flash(msg, 'error')
            return render_template('form.html', form=request.form, material_options=MATERIAL_OPTIONS)
        materiais_dict = extrair_materiais(request.form)
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO pontos
                (nome, rua, numero, complemento, bairro, cidade, estado, cep, materiais_json, horarios_inicio, horarios_fim)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                request.form['nome'], request.form['rua'], request.form['numero'], request.form.get('complemento',''),
                request.form['bairro'], request.form['cidade'], request.form['estado'], request.form['cep'],
                json.dumps(materiais_dict, ensure_ascii=False),
                request.form['horarios_inicio'], request.form['horarios_fim']
            ))
        flash('Ponto cadastrado com sucesso!', 'success')
        return redirect(url_for('pontos'))
    return render_template('form.html', form={}, material_options=MATERIAL_OPTIONS)

@app.route('/editar/<int:id>', methods=['GET','POST'])
def editar_ponto(id):
    with get_db_connection() as conn:
        ponto = conn.execute('SELECT * FROM pontos WHERE id=?', (id,)).fetchone()
    if not ponto:
        flash('Ponto não encontrado.', 'error')
        return redirect(url_for('pontos'))
    if request.method == 'POST':
        valido, msg = validar_formulario(request.form)
        if not valido:
            flash(msg, 'error')
            return render_template('form.html', form=request.form, material_options=MATERIAL_OPTIONS)
        materiais_dict = extrair_materiais(request.form)
        with get_db_connection() as conn:
            conn.execute('''
                UPDATE pontos SET
                nome=?, rua=?, numero=?, complemento=?, bairro=?, cidade=?, estado=?, cep=?,
                materiais_json=?, horarios_inicio=?, horarios_fim=?
                WHERE id=?
            ''', (
                request.form['nome'], request.form['rua'], request.form['numero'], request.form.get('complemento',''),
                request.form['bairro'], request.form['cidade'], request.form['estado'], request.form['cep'],
                json.dumps(materiais_dict, ensure_ascii=False),
                request.form['horarios_inicio'], request.form['horarios_fim'], id
            ))
        flash('Ponto atualizado com sucesso!', 'success')
        return redirect(url_for('pontos'))
    ponto_dict = dict(ponto)
    try:
        ponto_dict['materiais'] = json.loads(ponto_dict.get('materiais_json') or "{}")
    except:
        ponto_dict['materiais'] = {}
    return render_template('form.html', form=ponto_dict, material_options=MATERIAL_OPTIONS)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_ponto(id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM pontos WHERE id=?', (id,))
    flash('Ponto removido com sucesso!', 'success')
    return redirect(url_for('pontos'))

@app.route('/educacao')
def educacao():
    return render_template('educacao.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
