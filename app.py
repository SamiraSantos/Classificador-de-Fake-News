import argparse
import json
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import joblib

from classify import (
    DEFAULT_DATASET_PATH,
    DEFAULT_MIN_CONFIDENCE,
    DEFAULT_MODEL_PATH,
    DEFAULT_STRONG_MATCH_SIMILARITY,
    DEFAULT_MIN_SIMILARITY,
    build_dataset_index,
    classify_text,
)


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"


def find_available_port(start_port):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("Não foi encontrada uma porta livre.")


def load_classifier(model_path, dataset_path):
    model = joblib.load(model_path)
    dataset_index = build_dataset_index(model, dataset_path)
    return model, dataset_index


def make_handler(model, dataset_index, dataset_path):
    class FakeNewsHandler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            clean_path = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
            if not clean_path:
                clean_path = "index.html"
            target_path = (WEB_DIR / clean_path).resolve()
            web_root = WEB_DIR.resolve()

            try:
                target_path.relative_to(web_root)
            except ValueError:
                return str(WEB_DIR / "index.html")

            return str(target_path)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_POST(self):
            if self.path != "/api/classify":
                self.send_error(404, "Rota não encontrada")
                return

            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            try:
                try:
                    body = raw_body.decode("utf-8")
                except UnicodeDecodeError:
                    body = raw_body.decode("cp1252", errors="replace")

                payload = json.loads(body)
                text = (payload.get("text") or "").strip()
            except json.JSONDecodeError:
                self.send_json({"error": "JSON inválido."}, status=400)
                return

            if not text:
                self.send_json({"error": "Digite uma afirmação ou notícia."}, status=400)
                return

            result = classify_text(
                text,
                model,
                dataset_path=dataset_path,
                dataset_index=dataset_index,
                min_confidence=DEFAULT_MIN_CONFIDENCE,
                min_similarity=DEFAULT_MIN_SIMILARITY,
                strong_match_similarity=DEFAULT_STRONG_MATCH_SIMILARITY,
            )

            self.send_json(
                {
                    "classification": result["label"],
                    "confidence": round(result["display_confidence"] * 100),
                }
            )

        def send_json(self, payload, status=200):
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return FakeNewsHandler


def main():
    parser = argparse.ArgumentParser(description="Interface web local do detector de Fake News.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--dataset", default=DEFAULT_DATASET_PATH)
    args = parser.parse_args()

    model_path = str(ROOT_DIR / args.model)
    dataset_path = str(ROOT_DIR / args.dataset)

    print("Carregando modelo e dataset...", flush=True)
    model, dataset_index = load_classifier(model_path, dataset_path)
    port = find_available_port(args.port)
    handler = make_handler(model, dataset_index, dataset_path)
    server = ThreadingHTTPServer((args.host, port), handler)

    print(f"Interface aberta em: http://localhost:{port}", flush=True)
    print("Pressione Ctrl+C para encerrar.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
