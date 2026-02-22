#!/bin/bash
# Chạy tool với Python 3.11 + ddddocr
# Lần đầu: conda create -n pnj311 python=3.11 -y && conda activate pnj311 && pip install -r requirements.txt "ddddocr>=1.5,<1.6"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pnj311 2>/dev/null || {
  echo "Chạy lần đầu: conda create -n pnj311 python=3.11 -y"
  echo "Rồi: conda activate pnj311 && pip install -r requirements.txt \"ddddocr>=1.5,<1.6\""
  exit 1
}
python main.py "$@"
