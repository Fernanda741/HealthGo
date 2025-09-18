# HealthGo - Aplicação completa (versão simples frontend)

Esta entrega contém duas pastas: `backend` (Flask + SQLite) e `frontend` (React + Vite + Bootstrap).
O frontend consome a API do backend para upload de CSV, listagem de pacientes, consulta por paciente
com filtro por intervalo de tempo e download de CSV (completo ou filtrado).

## Como rodar (usando Docker Compose)

Certifique-se de ter Docker e docker-compose instalados.

Na raiz deste projeto (onde está o `docker-compose.yml`), rode:
```bash
docker-compose up --build
```

- Backend estará em: `http://localhost:5000`
- Frontend estará em: `http://localhost:3000` (servido por nginx no container; porte local mapeado para 3000)

## Endpoints úteis (backend)
- `POST /upload` -> Upload do CSV (form-data 'file')
- `GET /patients` -> Lista pacientes
- `GET /patients/<paciente_id>?start=HH:MM:SS&end=HH:MM:SS` -> Dados do paciente (filtrados opcionalmente)
- `GET /download/<paciente_id>?start=&end=` -> Retorna CSV (filtrado se start/end fornecidos)

Observe que o arquivo CSV enviado deve conter apenas um `paciente_id` por arquivo (conforme regra do teste).

## Observações
- O projeto usa SQLite (arquivo `healthgo.db` criado pelo backend).
- Os arquivos enviados ficam em `backend/uploads` (mapeado via volume).
