import os
import io
from datetime import datetime
import pandas as pd
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from database import db
from models import Paciente

UPLOAD_FOLDER = "uploads"
DB_PATH = "sqlite:///healthgo.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

def parse_timestamp(ts):
    # Try common formats, fallback to raw string
    for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            pass
    return None

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'no selected file'}), 400
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'only csv allowed'}), 400
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(save_path)

    df = pd.read_csv(save_path, dtype=str)
    # enforce columns lower-case trimming
    df.columns = [c.strip() for c in df.columns]

    if 'paciente_id' not in df.columns:
        return jsonify({'error': 'paciente_id column missing'}), 400
    # Only one patient per file rule
    unique_patients = df['paciente_id'].unique()
    if len(unique_patients) != 1:
        return jsonify({'error': 'file must contain exactly one paciente_id'}), 400

    # Append rows to DB
    for _, row in df.iterrows():
        # gracefully convert types
        try:
            paciente = Paciente(
                paciente_id=row.get('paciente_id'),
                paciente_nome=row.get('paciente_nome'),
                paciente_cpf=row.get('paciente_cpf'),
                hr=int(row.get('hr')) if row.get('hr') not in (None, '') else None,
                spo2=int(row.get('spo2')) if row.get('spo2') not in (None, '') else None,
                pressao_sys=int(row.get('pressao_sys')) if row.get('pressao_sys') not in (None, '') else None,
                pressao_dia=int(row.get('pressao_dia')) if row.get('pressao_dia') not in (None, '') else None,
                temp=float(row.get('temp')) if row.get('temp') not in (None, '') else None,
                resp_freq=int(row.get('resp_freq')) if row.get('resp_freq') not in (None, '') else None,
                status=row.get('status'),
                timestamp=row.get('timestamp')
            )
        except Exception as e:
            return jsonify({'error': f'failed parsing row: {e}'}), 400
        db.session.add(paciente)
    db.session.commit()
    return jsonify({'ok': True}), 201

@app.route('/patients', methods=['GET'])
def list_patients():
    rows = db.session.query(Paciente.paciente_id, Paciente.paciente_nome).distinct().all()
    result = [{'paciente_id': r[0], 'paciente_nome': r[1]} for r in rows]
    return jsonify(result)

@app.route('/patients/<paciente_id>', methods=['GET'])
def get_patient_data(paciente_id):
    start = request.args.get('start')  # expected format: ISO or HH:MM:SS
    end = request.args.get('end')
    query = Paciente.query.filter_by(paciente_id=paciente_id)
    # filter by timestamp if provided (string comparison may be unreliable)
    all_rows = query.all()
    # parse timestamps to datetime where possible
    records = []
    for r in all_rows:
        records.append({
            'id': r.id,
            'paciente_id': r.paciente_id,
            'paciente_nome': r.paciente_nome,
            'paciente_cpf': r.paciente_cpf,
            'hr': r.hr,
            'spo2': r.spo2,
            'pressao_sys': r.pressao_sys,
            'pressao_dia': r.pressao_dia,
            'temp': r.temp,
            'resp_freq': r.resp_freq,
            'status': r.status,
            'timestamp': r.timestamp
        })
    # if start/end provided, try to filter by parsing timestamps
    if start or end:
        def to_dt(ts):
            try:
                return parse_timestamp(ts)
            except:
                return None
        start_dt = parse_timestamp(start) if start else None
        end_dt = parse_timestamp(end) if end else None
        filtered = []
        for rec in records:
            rec_dt = to_dt(rec['timestamp'])
            if rec_dt is None:
                continue
            if start_dt and rec_dt < start_dt:
                continue
            if end_dt and rec_dt > end_dt:
                continue
            filtered.append(rec)
        # sort by timestamp
        filtered.sort(key=lambda x: x['timestamp'])
        return jsonify(filtered)
    # otherwise sort by timestamp string
    records.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '')
    return jsonify(records)

@app.route('/download/<paciente_id>', methods=['GET'])
def download_csv(paciente_id):
    start = request.args.get('start')
    end = request.args.get('end')
    # reuse get_patient_data logic by calling the function
    with app.test_request_context():
        # build query params
        # But simpler: fetch and filter here
        query = Paciente.query.filter_by(paciente_id=paciente_id).all()
        rows = []
        for r in query:
            rows.append({
                'paciente_id': r.paciente_id,
                'paciente_nome': r.paciente_nome,
                'paciente_cpf': r.paciente_cpf,
                'hr': r.hr,
                'spo2': r.spo2,
                'pressao_sys': r.pressao_sys,
                'pressao_dia': r.pressao_dia,
                'temp': r.temp,
                'resp_freq': r.resp_freq,
                'status': r.status,
                'timestamp': r.timestamp
            })
        # filter by start/end if provided (parse)
        if start or end:
            start_dt = parse_timestamp(start) if start else None
            end_dt = parse_timestamp(end) if end else None
            def to_dt(ts):
                try:
                    return parse_timestamp(ts)
                except:
                    return None
            rows = [r for r in rows if to_dt(r['timestamp']) is not None and (not start_dt or to_dt(r['timestamp']) >= start_dt) and (not end_dt or to_dt(r['timestamp']) <= end_dt)]
        # sort
        rows.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '')
        df = pd.DataFrame(rows)
        if df.empty:
            return jsonify({'error': 'no data found'}), 404
        # stream CSV
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'{paciente_id}_dados.csv')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
