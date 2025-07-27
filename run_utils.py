#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rdagent.scenarios.qlib.experiment.utils import generate_data_folder_from_qlib

if __name__ == "__main__":
    print("开始执行generate_data_folder_from_qlib()...")
    generate_data_folder_from_qlib()
    print("完成！") 