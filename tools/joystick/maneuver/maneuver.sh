#!/bin/bash

num="$1"

python3 -c "from . import Mem
mem = Mem()
if mem.maneuver_requested():
  print(\"already maneuvering\")
  exit()
mem.request(${num})
"
