#!/bin/bash
dir=$(cd "$(dirname "$0")"; pwd)
b=/admin.py
pid=/admin.pid

kill -9 `cat ${dir}${pid}`
echo 'restart ....'

echo ${dir}${b}
python ${dir}${b}
exit 0

