{
  inputs = {
    pkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {self, pkgs}@inp:
    let

      # Generate a user-friendly version number.
      version = builtins.substring 0 8 self.lastModifiedDate;

      # System types to support.
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];

      # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
      forAllSystems = pkgs.lib.genAttrs supportedSystems;

      # Nixpkgs instantiated for supported system types.
      nixpkgsFor = forAllSystems (system: import pkgs { inherit system; });
    in
    {
      # enter this python environment by executing `nix shell .`
      devShell = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
          import ./default.nix { inherit pkgs; }
      );
    };
}
