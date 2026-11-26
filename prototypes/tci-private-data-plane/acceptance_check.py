"""Current expanded quality evidence; historical RC.1 gate remains in V02-ACCEPTANCE-RESULT.json."""
import runpy
from pathlib import Path
if __name__=="__main__":
    runpy.run_path(str(Path(__file__).with_name("expanded_quality_check.py")),run_name="__main__")
