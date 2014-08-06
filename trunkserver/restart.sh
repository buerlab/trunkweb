#!/bin/bash
dir=$(cd "$(dirname "$0")"; pwd)
b=/trunkserver.py
pid=/this.pid

kill -9 `cat ${dir}${pid}`
echo 'restart ....'

echo ${dir}${b}
python ${dir}${b}
exit 0

