#!/bin/bash
for i in {1..50}
do
   nohup python3 main.py ai nv >> tetris.log 2>&1 &
done