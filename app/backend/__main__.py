"""Start the prototype: python -m app.backend [--port 8000]

Loads .env (for an optional ANTHROPIC_API_KEY), builds the data first if the warehouse does
not exist yet, then serves the frontend and API on http://127.0.0.1:<port>.
"""

import argparse

import uvicorn

from src.commentary.llm import load_env_file


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    load_env_file()
    from app.backend import main as backend  # imported after .env so the writer sees the key
    from src.pipeline import run as pipeline

    if not backend.settings.warehouse_path.exists():
        print("No warehouse yet - running the pipeline once...")
        pipeline.run()
    print(f"Open http://127.0.0.1:{args.port}")
    uvicorn.run(backend.app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
