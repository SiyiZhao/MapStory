#!/usr/bin/env bash
set -euo pipefail
DB="mystory.db"

python mapstory.py --db "$DB" add --time=-380 --event "齐桓公建稷下学宫" --priority doubt

python mapstory.py --db "$DB" add --time=-283 --event "燕拜乐毅上将军，五国攻齐" --persons "乐毅" --priority doubt
python mapstory.py --db "$DB" add --time=-283 --event "李斯生于楚" --persons "李斯" --priority doubt
python mapstory.py --db "$DB" add --time=-283 --event "庾秉生于魏" --persons "庾秉" --priority fanon

python mapstory.py --db "$DB" add --time=-282 --event "燕秦开却东胡，始置上谷郡" --priority doubt
python mapstory.py --db "$DB" add --time=-282 --event "齐襄王田法章立" --persons "田法章" --priority doubt

python mapstory.py --db "$DB" add --time=-194-06-01 --time-note "汉十二年四月甲辰二十五日" --lat 34.34 --lon 108.94 --location-note "长乐宫（今西安汉长安城）" --event "刘邦崩于长乐宫；卢绾闻讯逃匈奴，被冒顿封东胡卢王" --persons "刘邦, 卢绾, 冒顿" --priority fact