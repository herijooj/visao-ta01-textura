{
  description = "visao-textura: classificação por textura — filtros clássicos + KMeans";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
  in {
    devShells.${system}.default = pkgs.mkShell {
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
    };
  };
}
