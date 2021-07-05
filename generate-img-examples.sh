#!/bin/bash

# Generates examples for all example/img

. env/bin/activate

for name in $(ls example/img)
do
    python3 generate.py -i example/img/$name/$name.png -o example/img/$name &
    python3 generate.py -i example/img/$name/$name.jpg -o example/img/$name &
done