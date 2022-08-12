{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.aquaorder;

  nginxProxyAddress =
    let
      addr = head cfg.listenAddresses;
    in
      if hasInfix "/" addr then
        "unix:${addr}:"
      else
        head addr
      ;
in
{

  options = {
    services.aquaorder = {
      enable = mkEnableOption "aquaorder server";

      package = mkOption {
        type = types.package;
        default = pkgs.python3.pkgs.callPackage ./. {};
        defaultText = literalExpression "pkgs.python3.pkgs.callPackage ./. {}";
        description = "The aquaorder package to use.";
      };

      listenAddresses = mkOption {
        type = types.nonEmptyListOf types.str;
        default = [ "/run/aquaorder.socket" ];
        description = ''
          The IP address or socket path on which aquaorder will listen.
          By default listens on localhost.
        '';
        example = [ "[::1]:8000" ];
      };

      articlesFile = mkOption {
        type = types.path;
        description = ''
          Path to the YAML file to load articles from.
        '';
      };

      suppliersFile = mkOption {
        type = types.path;
        description = ''
          Path to the YAML file to load supplier info from.
        '';
      };

      nginx = {
        enable = mkOption {
          type = types.bool;
          default = false;
          description = ''
            Configure the nginx reverse proxy settings.
          '';
        };

        hostName = mkOption {
          type = types.str;
          description = ''
            The hostname to use to setup the virtualhost configuration
          '';
        };

        path = mkOption {
          type = types.str;
          default = "/";
          description = ''
            The path to use to setup the virtualhost configuration
          '';
        };
      };

    };

  };

  config = mkIf cfg.enable (
    mkMerge [
      {
        meta.maintainers = with lib.maintainers; [ schnusch ];

        systemd.sockets.aquaorder = {
          wantedBy = [ "sockets.target" ];
          socketConfig.ListenStream = cfg.listenAddresses;
        };

        systemd.services.aquaorder = {
          description = "aquaorder server";
          serviceConfig = {
            User = "aquaorder";
            Group = "aquaorder";
            DynamicUser = "yes";
            StateDirectory = "aquaorder";
            StateDirectoryMode = "0755";
            PrivateDevices = true;
            # Sandboxing
            CapabilityBoundingSet = "CAP_NET_RAW CAP_NET_ADMIN";
            ProtectSystem = "strict";
            ProtectHome = true;
            PrivateTmp = true;
            ProtectKernelTunables = true;
            ProtectKernelModules = true;
            ProtectControlGroups = true;
            RestrictAddressFamilies = "AF_INET AF_INET6 AF_UNIX AF_PACKET AF_NETLINK";
            RestrictNamespaces = true;
            LockPersonality = true;
            MemoryDenyWriteExecute = true;
            RestrictRealtime = true;
            RestrictSUIDSGID = true;
            ExecStart = ''
              ${cfg.package}/bin/aquaorder \
                --articles ${escapeShellArg cfg.articlesFile} \
                --suppliers ${escapeShellArg cfg.suppliersFile} \
                --systemd
            '';
          };
        };
      }

      (
        mkIf cfg.nginx.enable {
          services.nginx = {
            enable = true;
            virtualHosts."${cfg.nginx.hostName}" = {
              locations."${cfg.nginx.path}" = {
                proxyPass = "http://${nginxProxyAddress}/";
              };
            };
          };
        }
      )
    ]
  );
}
