from flask import Flask, render_template_string, request, redirect, url_for, flash
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'bicicletaria_secret_key'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'servicos.json')

def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

def load_servicos():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_servicos(servicos):
    with open(DATA_FILE, 'w') as f:
        json.dump(servicos, f, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bicicletaria</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; text-align: center; }
        .nav { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        .nav a { padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        .nav a:hover { background: #45a049; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { resize: vertical; min-height: 80px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        .btn-excluir { background: #f44336; }
        .btn-excluir:hover { background: #da190b; }
        .btn-concluir { background: #2196F3; }
        .btn-concluir:hover { background: #1976D2; }
        .servico-item { background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .servico-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .servico-cliente { font-size: 1.1em; font-weight: bold; color: #333; }
        .servico-data { color: #666; font-size: 0.9em; }
        .servico-desc { color: #555; margin: 5px 0; }
        .servico-tipo { color: #4CAF50; font-weight: bold; }
        .servico-foto { max-width: 200px; max-height: 150px; border-radius: 4px; margin-top: 10px; }
        .servico-actions { display: flex; gap: 10px; margin-top: 10px; }
        .empty { text-align: center; color: #666; padding: 40px; }
        .flash { padding: 10px; background: #4CAF50; color: white; margin-bottom: 15px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bicicletaria</h1>
        <div class="nav">
            <a href="/">Novo Servico</a>
            <a href="/fila">Fila de Servicos</a>
        </div>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

INDEX_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
<form method="POST" enctype="multipart/form-data">
    <div class="card">
        <h2>Novo Servico</h2>
        <div class="form-group">
            <label for="nome_cliente">Nome do Cliente:</label>
            <input type="text" id="nome_cliente" name="nome_cliente" required>
        </div>
        <div class="form-group">
            <label for="data">Data:</label>
            <input type="date" id="data" name="data" value="{{ data_atual }}" required>
        </div>
        <div class="form-group">
            <label for="descricao">Descricao da Bicicleta:</label>
            <textarea id="descricao" name="descricao" required></textarea>
        </div>
        <div class="form-group">
            <label for="servico">Servico a Executar:</label>
            <select id="servico" name="servico" required>
                <option value="">Selecione...</option>
                <option value="Manutencao">Manutencao</option>
                <option value="Reparo">Reparo</option>
                <option value="Troca de Pecas">Troca de Pecas</option>
                <option value="Limpeza">Limpeza</option>
                <option value="Upgrade">Upgrade</option>
                <option value="Outro">Outro</option>
            </select>
        </div>
        <div class="form-group">
            <label for="foto">Foto da Bicicleta:</label>
            <input type="file" id="foto" name="foto" accept="image/*">
        </div>
        <button type="submit">Registrar Servico</button>
    </div>
</form>
''')

FILA_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
<h2>Fila de Servicos</h2>
{% if servicos %}
    {% for servico in servicos %}
        <div class="servico-item">
            <div class="servico-header">
                <span class="servico-cliente">{{ servico.nome_cliente }}</span>
                <span class="servico-data">{{ servico.data }}</span>
            </div>
            <div class="servico-desc"><strong>Bicicleta:</strong> {{ servico.descricao }}</div>
            <div class="servico-tipo"><strong>Servico:</strong> {{ servico.servico }}</div>
            {% if servico.foto %}
                <img src="{{ url_for('static', filename='uploads/' + servico.foto) }}" class="servico-foto" alt="Foto">
            {% endif %}
            <div class="servico-actions">
                <form method="POST" action="/concluir/{{ servico.id }}">
                    <button type="submit" class="btn-concluir">Marcar como Executado</button>
                </form>
                <form method="POST" action="/excluir/{{ servico.id }}">
                    <button type="submit" class="btn-excluir" onclick="return confirm('Excluir este registro?')">Excluir</button>
                </form>
            </div>
        </div>
    {% endfor %}
{% else %}
    <div class="empty">Nenhum servico na fila.</div>
{% endif %}
''')

@app.route('/')
def index():
    data_atual = datetime.now().strftime('%Y-%m-%d')
    return render_template_string(INDEX_TEMPLATE, data_atual=data_atual)

@app.route('/', methods=['POST'])
def criar_servico():
    nome_cliente = request.form['nome_cliente']
    data = request.form['data']
    descricao = request.form['descricao']
    servico = request.form['servico']
    
    filename = None
    if 'foto' in request.files:
        file = request.files['foto']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    servicos = load_servicos()
    new_id = max([s['id'] for s in servicos], default=0) + 1
    servicos.append({
        'id': new_id,
        'nome_cliente': nome_cliente,
        'data': data,
        'descricao': descricao,
        'servico': servico,
        'foto': filename,
        'executado': False
    })
    save_servicos(servicos)
    
    flash('Servico registrado com sucesso!')
    return redirect(url_for('index'))

@app.route('/fila')
def fila():
    servicos = [s for s in load_servicos() if not s.get('executado', False)]
    servicos.reverse()
    return render_template_string(FILA_TEMPLATE, servicos=servicos)

@app.route('/concluir/<int:id>')
def concluir(id):
    servicos = load_servicos()
    for s in servicos:
        if s['id'] == id:
            s['executado'] = True
            break
    save_servicos(servicos)
    flash('Servico marcado como executado!')
    return redirect(url_for('fila'))

@app.route('/excluir/<int:id>')
def excluir(id):
    servicos = load_servicos()
    for i, s in enumerate(servicos):
        if s['id'] == id:
            if s.get('foto'):
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], s['foto']))
                except:
                    pass
            servicos.pop(i)
            break
    save_servicos(servicos)
    flash('Servico excluido!')
    return redirect(url_for('fila'))

if __name__ == '__main__':
    init_data()
    app.run(host='0.0.0.0', port=5000)