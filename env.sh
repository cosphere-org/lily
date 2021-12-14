#! /bin/bash

export CFLAGS=$(pkg-config --cflags hunspell)
export LDFLAGS=$(pkg-config --libs hunspell)
