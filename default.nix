{ lib
, buildPythonApplication
, pythonOlder

, aiohttp
, jinja2
, jsonschema
, systemd
, pyyaml

, black
, flake8
, mypy
, sassc
}:

buildPythonApplication {
  pname = "aquaorder";
  version = "0.0.0";

  disabled = pythonOlder "3.8";

  src = ./.;

  propagatedBuildInputs = [
    aiohttp
    jinja2
    jsonschema
    systemd
    pyyaml
  ];

  nativeBuildInputs = [
    black
    flake8
    mypy
    sassc
  ];

  pythonImportsCheck = [ "aqua.order" ];

  meta = with lib; {
    description = "...";
    license = licenses.agpl3Plus;
    maintainers = with maintainers; [ schnusch ];
  };
}
