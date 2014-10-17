#!/bin/bash
dir=$(cd "$(dirname "$0")"; pwd)
b=/server.py
pid=/this.pid

kill -9 `cat ${dir}${pid}`
echo 'restart ....'

echo ${dir}${b}
setsid python ${dir}${b}
exit 0

