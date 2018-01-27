# mipt1.ru parser

## Description

Rips all the content from mipt1.ru state physics exam notes and compiles them into several `.tex` files, complete with
images

## How to use

    python3 mipt1.py manifest.json && pdflatex main.tex

Creates several files (filenames can be modified in `manifest.json`, but then the `main.tex` should be modified as
well).
