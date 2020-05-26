# LSP-promql

PromQL support for Sublime LSP plugin, using [promql-langserver](https://github.com/prometheus-community/promql-langserver).

## Usage

![movie](https://github.com/nevill/LSP-promql/raw/master/screenshots/yaml.gif)


## Installation

1. Put `promql-langserver` binary under your $PATH.
```bash
git clone https://github.com/prometheus-community/promql-langserver

cd promql-langserver

# have GO installed
go build ./cmd/...

cp promql-langserver <One of your $PATH>
```
2. Install package `LSP`, `LSP-promql` via `package control`.
3. Start editing .promql file.


## Settings

* Set Prometheus server via `env.LANGSERVER_PROMETHEUSURL`
```json
{
  "env": {
    "LANGSERVER_PROMETHEUSURL": "http://localhost:9090"
  }
}
```
