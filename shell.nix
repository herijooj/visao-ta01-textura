{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "visao-textura";
  buildInputs = [
    (pkgs.python312.withPackages (ps: with ps; [
      numpy
      opencv4
      scikit-learn
      pillow
      matplotlib
    ]))
    pkgs.git
  ];
  shellHook = ''
    echo "visao-textura pronto: python $(python --version 2>&1) | cv2 + sklearn ok"
  '';
}
