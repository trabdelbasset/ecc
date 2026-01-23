{
  nixConfig = {
    extra-trusted-substituters = [
      "https://serve.eminrepo.cc/"
    ];
    extra-trusted-public-keys = [ "serve.eminrepo.cc:fgdTGDMn75Z0NOvTmus/Z9Fyh6ExgoqddNVkaYVi5qk=" ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    parts.url = "github:hercules-ci/flake-parts";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    infra.url = "github:Emin017/ieda-infra";
  };

  outputs =
    inputs@{
      nixpkgs,
      parts,
      treefmt-nix,
      infra,
      ...
    }:
    parts.lib.mkFlake { inherit inputs; } {
      imports = [
        treefmt-nix.flakeModule
      ];
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      flake.hydraJobs = {
        x86_64-linux = {
          iedaUnstable = inputs.self.packages.x86_64-linux.iedaUnstable;
          magic-vlsi = inputs.nixpkgs.legacyPackages.x86_64-linux.magic-vlsi;
          yosysWithSlang = inputs.self.packages.x86_64-linux.yosysWithSlang;
        };
      };
      perSystem =
        {
          inputs',
          self',
          config,
          pkgs,
          system,
          ...
        }:
        {
          _module.args.pkgs = import inputs.nixpkgs {
            inherit system;
          };
          # Use `nix develop -c python3 test/test_tools_yosys.py` to run tests in dev shell
          devShells = {
            default = pkgs.mkShell {
              inputsFrom = [ inputs'.infra.packages.iedaUnstable ];
              nativeBuildInputs =
                with pkgs;
                [
                  git
                  black
                  isort
                  uv
                  cargo
                ] ++ [
                  inputs'.infra.packages.yosysWithSlang
                ];
              shellHook = ''
                ENABLE_OSS_CAD_SUITE=false ./build.sh
                source .venv/bin/activate
              '';
            };
          };
          packages = {
            yosysWithSlang = inputs'.infra.packages.yosysWithSlang;
            ieda = inputs'.infra.packages.iedaUnstable;
          };
        };
    };
}
