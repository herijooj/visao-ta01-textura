{ pkgs ? import <nixpkgs> {} }:

# Ambiente mínimo: só o interpretador Python vem do nix.
# numpy/opencv/sklearn/etc vêm via pip (wheels manylinux, ~200MB),
# em vez de via nix (pkgs.opencv4 puxa Qt + ffmpeg + GTK = ~4GB de closure).
pkgs.mkShell {
  name = "visao-textura";
  packages = [
    pkgs.python312
    # libstdc++ + libz para os wheels manylinux do pip (numpy/opencv)
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];
  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:"$LD_LIBRARY_PATH"
    if [ ! -d .venv ]; then
      python -m venv .venv
      # shellcheck disable=SC1091
      source .venv/bin/activate
      pip install -r requirements.txt
    else
      # shellcheck disable=SC1091
      source .venv/bin/activate
      python -c "import cv2, sklearn, PIL, matplotlib" 2>/dev/null || pip install -r requirements.txt
    fi
    echo "visao-textura pronto: $(python --version 2>&1) | venv ativo"
  '';
}
