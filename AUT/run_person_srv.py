import os
import sys

# Make sure this file's own directory is on sys.path, so the "app" package
# resolves regardless of the working directory this script is launched
# from (e.g. an IDE run configuration whose working directory defaults to
# the project root instead of this folder). This line runs again in the
# reloader's subprocess too, since it sits outside the __main__ guard.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
