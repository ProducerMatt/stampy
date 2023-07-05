{
  description = "Application packaged using poetry2nix";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        inherit (poetry2nix.legacyPackages.${system}) mkPoetryApplication mkPoetryEnv defaultPoetryOverrides;
        pkgs = nixpkgs.legacyPackages.${system};
        appSettings = {
          projectDir = self;
          python = pkgs.python311;
          overrides = defaultPoetryOverrides.extend
            (self: super: {
              discord-py = super.discord-py.overridePythonAttrs
                (
                  old: {
                    buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                  }
                );
            });
        };
        #app = mkPoetryApplication appSettings;
        shell = (mkPoetryEnv appSettings).env.overrideAttrs (oldAttrs: {
          buildInputs = [ poetry2nix.packages.${system}.poetry ];
        })
        ;
      in
        {
          #packages = {
          #  stampy = app;
          #  default = self.packages.${system}.stampy;
          #};

          devShells.default = shell;
        });
}
