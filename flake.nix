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
        inherit (poetry2nix.legacyPackages.${system}) mkPoetryPackages mkPoetryEnv defaultPoetryOverrides;
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python39;
        pythonPkgs = pkgs.python39Packages;
        appSettings = {
          inherit python;
          projectDir = self;
          overrides = defaultPoetryOverrides.extend
            (self: super: rec {
              # package databases-0.7 is broken with sqlalchemy 2
              #flask = pythonPkgs.flask;
              #gitpython = pythonPkgs.gitpython;
              #black = pythonPkgs.black;
              #google-api-python-client = pythonPkgs.google-api-python-client;
              #google-auth-oauthlib = pythonPkgs.google-auth-oauthlib;
              #jellyfish = pythonPkgs.jellyfish;
              #lxml = pythonPkgs.lxml;
              #numpy = pythonPkgs.numpy;
              #openai = pythonPkgs.openai;
              #pandas = pythonPkgs.pandas;
              #psutil = pythonPkgs.psutil;
              #python-dotenv = pythonPkgs.python-dotenv;
              #slack-sdk = pythonPkgs.slack-sdk;
              #structlog = pythonPkgs.structlog;
              transformers = pythonPkgs.transformers;
              maturin = pythonPkgs.buildPythonPackage rec {
                pname = "maturin";
                version = "1.1.0";
                src = pkgs.fetchPypi {
                  inherit pname version;
                  sha256 = "sha256-RlCuqo3r0AS1Wq56+3UkjL1NYc19otz06tiyK1jOyuA=";
                };
                doCheck = true;
                format = "pyproject";
                propagatedBuildInputs = [
                  pkgs.maturin
                  self.setuptools
                  self.tomli
                  self.setuptools-rust
                ];
              };
              #maturin =
              #  let
              #    verinfo = {
              #      rev = "2e7b36a";
              #      owner = "PyO3";
              #      repo = "maturin";
              #      hash = "sha256-UH+qOKKQdWXQZZMtrihbWmKaUoSy1NciGh9UTtS/W5E=";
              #    };
              #    src = pkgs.fetchFromGitHub {
              #      inherit (verinfo) owner repo rev hash;
              #    };
              #  in
              #    (mkPoetryPackages {
              #      projectDir = src;
              #    }).poetryPackages.maturin;
              discord-py = super.discordpy.overridePythonAttrs
                (
                  old: {
                    buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
                  }
                );
              jellyfish = super.jellyfish.overridePythonAttrs
                (
                  old:
                    { buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.maturin self.maturin ]; }
                );
              safetensors =
                (
                  old: {
                    buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
                  }
                );
              codaio =
                let
                  verinfo = {
                    rev = "424d226";
                    owner = "Blasterai";
                    repo = "codaio";
                    hash = "sha256-t/OSWzXtx+5ZdnL2QTnVLILoh4+rtpHMAcU4wm0tT9U=";
                  };
                  src = pkgs.fetchFromGitHub {
                    inherit (verinfo) owner repo rev hash;
                  };
                in
                  mkPoetryPackages {
                    projectDir = src;
                  };
              helicone =
                let
                  verinfo = {
                    rev = "afb1ae3";
                    owner = "Helicone";
                    repo = "helicone";
                    hash = "";
                  };
                  src = pkgs.fetchFromGitHub {
                    inherit (verinfo) owner repo rev hash;
                  };
                in
                  mkPoetryPackages {
                    projectDir = src + ./helicone-python;
                  };
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
