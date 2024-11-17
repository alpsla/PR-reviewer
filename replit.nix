{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.glibcLocales
    pkgs.pkg-config
    pkgs.libffi
    pkgs.cacert
    pkgs.postgresql
    pkgs.openssl
  ];
}
