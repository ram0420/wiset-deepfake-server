#!/bin/bash
uvicorn app.main:app --host=0.0.0.0 --port=10000

# #!/bin/bash
# uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}
