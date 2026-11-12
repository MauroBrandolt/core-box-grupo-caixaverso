"""Login, recuperacao de senha e troca de celular."""
import datetime
import random

from flask import Blueprint, render_template, request, make_response, jsonify, redirect

from app import auditoria
from app.db import get_db
from app.seguranca import verificar_senha, emitir_token, hash_senha

bp = Blueprint("auth", __name__)


def _autenticar(cpf, senha):
    """Retorna (usuario, erro, status_http)."""
    db = get_db()
    agora = datetime.datetime.now()

    tentativa = db.execute(
        "SELECT falhas, bloqueado_ate FROM tentativas_login WHERE cpf = ?",
        (cpf,),
    ).fetchone()

    if tentativa and tentativa["bloqueado_ate"]:
        try:
            bloqueado_ate = datetime.datetime.fromisoformat(
                tentativa["bloqueado_ate"]
            )
        except ValueError:
            bloqueado_ate = agora

        if bloqueado_ate > agora:
            return None, "Acesso temporariamente bloqueado.", 429

        db.execute(
            "DELETE FROM tentativas_login WHERE cpf = ?",
            (cpf,),
        )
        db.commit()
        tentativa = None

    usuario = db.execute(
        "SELECT * FROM usuarios WHERE cpf = ?",
        (cpf,),
    ).fetchone()

    credencial_valida = (
        usuario is not None
        and verificar_senha(senha, usuario["senha_hash"])
    )

    if not credencial_valida:
        falhas = (tentativa["falhas"] if tentativa else 0) + 1
        bloqueado_ate = None

        if falhas >= 5:
            bloqueado_ate = (
                agora + datetime.timedelta(minutes=15)
            ).isoformat(timespec="seconds")

        db.execute(
            """
            INSERT INTO tentativas_login (cpf, falhas, bloqueado_ate)
            VALUES (?, ?, ?)
            ON CONFLICT(cpf) DO UPDATE SET
                falhas = excluded.falhas,
                bloqueado_ate = excluded.bloqueado_ate
            """,
            (cpf, falhas, bloqueado_ate),
        )
        db.commit()

        status = 429 if bloqueado_ate else 401
        mensagem = (
            "Acesso temporariamente bloqueado."
            if bloqueado_ate
            else "Credenciais inválidas."
        )
        return None, mensagem, status

    db.execute(
        "DELETE FROM tentativas_login WHERE cpf = ?",
        (cpf,),
    )
    db.commit()

    return usuario, None, 200


def _vincular_dispositivo(usuario):
    # TM-25: vínculo automático de qualquer dispositivo, sem step-up
    db = get_db()
    db.execute("INSERT INTO dispositivos (usuario_id, descricao, vinculado_em) VALUES (?,?,?)",
               (usuario["id"], request.headers.get("User-Agent", "desconhecido")[:80],
                datetime.datetime.now().isoformat(timespec="seconds")))
    db.commit()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    cpf = request.form.get("cpf", "").strip()
    senha = request.form.get("senha", "")
    usuario, erro, status = _autenticar(cpf, senha)
    if erro:
        return render_template("login.html", erro=erro, cpf=cpf), status
    token = emitir_token(usuario)
    _vincular_dispositivo(usuario)
    auditoria.registrar(cpf, "LOGIN_OK", {"cpf": cpf, "token": token, "ip": request.remote_addr})
    resp = make_response(redirect("/home"))
    # Cookie sem HttpOnly/Secure/SameSite (achado típico de DAST no Dia 02/03)
    resp.set_cookie(
        "box_token",
        token,
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    return resp


@bp.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    dados = request.get_json(force=True)
    usuario, erro, status = _autenticar(dados.get("cpf", ""), dados.get("senha", ""))
    if erro:
        return jsonify({"erro": erro}), status
    token = emitir_token(usuario)
    auditoria.registrar(usuario["cpf"], "LOGIN_API_OK", {"token": token})
    return jsonify({"token": token, "tipo": "Bearer", "expira_em_horas": 168})


@bp.route("/logout")
def logout():
    resp = make_response(redirect("/login"))
    resp.delete_cookie(
        "box_token",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    return resp


@bp.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "GET":
        return render_template("recuperar.html", etapa="dados")
    db = get_db()
    cpf = request.form.get("cpf", "").strip()
    nascimento = request.form.get("nascimento", "").strip()
    usuario = db.execute("SELECT * FROM usuarios WHERE cpf = ? AND nascimento = ?",
                         (cpf, nascimento)).fetchone()
    if not usuario:
        return render_template("recuperar.html", etapa="dados", erro="Dados não conferem."), 400
    # TM-02: OTP de 4 dígitos, gerador não criptográfico, válido por 24h
    codigo = f"{random.randint(0, 9999):04d}"
    expira = (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat()
    db.execute("INSERT OR REPLACE INTO otp (cpf, codigo, expira_em) VALUES (?,?,?)", (cpf, codigo, expira))
    db.commit()
    auditoria.registrar(cpf, "OTP_ENVIADO", {"celular": usuario["celular"], "codigo": codigo})
    return render_template("recuperar.html", etapa="codigo", cpf=cpf, celular=usuario["celular"])


@bp.route("/recuperar/confirmar", methods=["POST"])
def recuperar_confirmar():
    db = get_db()
    cpf = request.form.get("cpf", "")
    otp = db.execute("SELECT * FROM otp WHERE cpf = ? AND codigo = ?",
                     (cpf, request.form.get("codigo", ""))).fetchone()
    if not otp:
        return render_template("recuperar.html", etapa="codigo", cpf=cpf, erro="Código inválido."), 400
    db.execute("UPDATE usuarios SET senha_hash = ? WHERE cpf = ?",
               (hash_senha(request.form.get("nova_senha", "")), cpf))
    db.commit()
    # TM-02: sessões/tokens antigos continuam válidos (JWT sem revogação)
    return render_template("recuperar.html", etapa="ok")


@bp.route("/recuperar/trocar-celular", methods=["POST"])
def trocar_celular():
    db = get_db()
    cpf = request.form.get("cpf", "")
    nome_mae = request.form.get("nome_mae", "")
    novo = request.form.get("novo_celular", "")
    # TM-02 (T2-D): troca de celular só com CPF + nome da mãe
    u = db.execute("SELECT id FROM usuarios WHERE cpf = ? AND nome_mae = ?", (cpf, nome_mae)).fetchone()
    if not u:
        return render_template("recuperar.html", etapa="dados", erro="Dados não conferem."), 400
    db.execute("UPDATE usuarios SET celular = ? WHERE id = ?", (novo, u["id"]))
    db.commit()
    return render_template("recuperar.html", etapa="dados", info="Celular atualizado com sucesso!")
