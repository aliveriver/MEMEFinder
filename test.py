from pathlib import Path 
from paddlenlp import Taskflow 

models_dir = Path(r'D:\MEMEFinder\models\senta') 
models_dir.mkdir(parents=True, exist_ok=True) 

print('TASKFLOW_HOME:', models_dir) 
try: 
    t = Taskflow("sentiment_analysis", task_path=str(models_dir)) 
    print('Taskflow 初始化成功') 
except Exception as e: 
    print('Taskflow 初始化失败:', e)