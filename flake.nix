{
  inputs = {
    pkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {self, pkgs}@inp:
    let
      l = pkgs.lib // builtins;
      supportedSystems = [ "x86_64-linux" "aarch64-darwin" ];
      #forAllSystems = f: l.genAttrs supportedSystems
      #  (system: f system (import pkgs {inherit system;}));
      forAllSystems = pkgs.lib.genAttrs supportedSystems;
      nixpkgsFor = forAllSystems (system: import pkgs { inherit system; });
    in
    {
      # enter this python environment by executing `nix shell .`
      devShell = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
        import ./default.nix { inherit pkgs; pythonPackages = pkgs.python311Packages; }
      );
    };
}
