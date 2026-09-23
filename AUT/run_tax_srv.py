import os
import sys

# Same sys.path fix as run.py: the "app" and "tax_app" packages must resolve
# regardless of the working directory (tax_app reuses app.auth).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("tax_app.main:app", host="127.0.0.1", port=8001, reload=True)
