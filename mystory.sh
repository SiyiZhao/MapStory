#!/usr/bin/env bash
set -euo pipefail
DB="mystory.db"

python mapstory.py --db "$DB" add --time "-381" --event "齐桓公建稷下学宫" --priority doubt

python mapstory.py --db "$DB" add --time "-284" --event "燕拜乐毅上将军，五国攻齐" --persons "乐毅" --priority doubt
python mapstory.py --db "$DB" add --time "-284" --event "李斯生于楚" --persons "李斯" --priority doubt
python mapstory.py --db "$DB" add --time "-284" --event "庾秉生于魏" --persons "庾秉" --priority fanon

python mapstory.py --db "$DB" add --time "-283" --event "燕秦开却东胡，始置上谷郡" --priority doubt
python mapstory.py --db "$DB" add --time "-283" --event "齐襄王田法章立" --persons "田法章" --priority doubt
