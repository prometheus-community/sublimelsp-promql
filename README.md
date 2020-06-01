# LSP-promql

PromQL support for Sublime LSP plugin, using [promql-langserver](https://github.com/prometheus-community/promql-langserver).

## Usage

![movie](https://github.com/nevill/LSP-promql/raw/master/screenshots/promql.gif)


## Installation

1. Install `LSP-promql` via package control.
2. It will download binary `promql-langserver` automatically.
3. Restart Sublime Text.

## Settings

* Set Prometheus server via `env.LANGSERVER_PROMETHEUSURL` in Packages Settings -> LSP -> Servers -> LSP-promql
```json
{
  "env": {
    "LANGSERVER_PROMETHEUSURL": "http://localhost:9090"
  }
}
```
