"""Core Box: aplicacao de laboratorio. Nao usar em producao."""

import logging

from flask import Flask, jsonify, redirect, request
from werkzeug.exceptions import HTTPException

from app import config, db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(config.Config)

    if test_config:
        app.config.update(test_config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    db.init_app(app)

    from app.auth import bp as auth_bp
    from app.contas import bp as contas_bp
    from app.pix import bp as pix_bp
    from app.backoffice import bp as backoffice_bp
    from app.onboarding import bp as onboarding_bp
    from app.api_interna import bp as interna_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(pix_bp)
    app.register_blueprint(backoffice_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(interna_bp)

    @app.route("/")
    def index():
        return redirect("/login")

    @app.route("/health")
    def health():
        # Nao divulgar versao, ambiente ou estado do debugger.
        return {"status": "ok", "app": "core-box"}

    @app.errorhandler(Exception)
    def erro_generico(exc):
        # Preserva erros HTTP, como 404 e 405, e seus cabecalhos.
        # Uma pagina inexistente nao deve virar erro interno.
        if isinstance(exc, HTTPException) and exc.code < 500:
            return exc

        # Detalhes ficam somente nos logs do servidor.
        app.logger.exception("Erro interno nao tratado")

        return jsonify({"erro": "Erro interno do servidor"}), 500

    @app.after_request
    def aplicar_cabecalhos_seguranca(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Scripts e estilos devem ser carregados da propria origem.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "frame-src 'none'"
        )

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Nao permitir cache de paginas e respostas potencialmente sensiveis.
        # Arquivos estaticos mantem a politica de cache do Flask.
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"

        return response

    return app
