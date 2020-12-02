#!/bin/bash
for i in {1..3}
do
   python3 main.py ai nv &
   #nohup python3 main.py ai nv >> tetris.log 2>&1 &
done
