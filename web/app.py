from flask import Flask, render_template, request, abort
from db.supabase_client import listar_eventos, obter_evento_por_url_evento

app = Flask(__name__)

@app.get("/")
def index():
    q = request.args.get("q")
    categoria = request.args.get("categoria")
    principal = request.args.get("principal")
    principal_flag = True if principal == "1" else None
    
    page = request.args.get("page", 1, type=int)
    per_page = 18
    
    eventos_all = listar_eventos(limit=1000, categoria=categoria or None, q=q or None, principal=principal_flag)
    
    total_eventos = len(eventos_all)
    total_pages = (total_eventos + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1
        
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    eventos = eventos_all[start_idx:end_idx]

    return render_template("index.html", eventos=eventos, q=q if q else "", categoria=categoria if categoria else "", principal=principal, page=page, total_pages=total_pages, total_eventos=total_eventos)

@app.get("/evento")
def evento():
    url_evento = request.args.get("url")
    if not url_evento:
        abort(400)

    ev = obter_evento_por_url_evento(url_evento)
    if not ev:
        abort(404)

    return render_template("evento.html", ev=ev)
    
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)