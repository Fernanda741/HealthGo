from database import db

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.String(50), index=True)
    paciente_nome = db.Column(db.String(100))
    paciente_cpf = db.Column(db.String(20))
    hr = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    pressao_sys = db.Column(db.Integer)
    pressao_dia = db.Column(db.Integer)
    temp = db.Column(db.Float)
    resp_freq = db.Column(db.Integer)
    status = db.Column(db.String(20))
    timestamp = db.Column(db.String(50), index=True)
