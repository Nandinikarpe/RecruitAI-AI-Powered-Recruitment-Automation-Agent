"""Load .env then Streamlit Cloud secrets into os.environ so auth can read Supabase + JWT keys."""

import os


def apply_streamlit_secrets_to_environ() -> None:
    """Call once at app startup (after `import streamlit`). Safe on local runs without secrets."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    try:
        import streamlit as st

        for k, v in dict(st.secrets).items():
            if isinstance(v, (str, int, float)):
                os.environ.setdefault(str(k), str(v))
            elif isinstance(v, bool):
                os.environ.setdefault(str(k), "true" if v else "false")
    except Exception:
        pass
