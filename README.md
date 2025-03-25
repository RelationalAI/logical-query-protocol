# Logical Query Protocol

[[Design document](https://docs.google.com/document/d/1QXRU7zc1SUvYkyMCG0KZINZtFgzWsl9-XHxMssdXZzg)]

## Validate

We use the [buf utility](https://buf.build/docs/cli/quickstart/) to [validate and
lint](https://buf.build/docs/cli/quickstart/#lint-your-api) the
protobuf specification. Just follow the linked instructions and then run

```
buf lint
```

To ensure the specifications remain backward and forward compatible, you’ll want to check
for breaking changes. Protobuf itself enforces some rules (e.g., don’t reuse field numbers),
but `buf` takes this further with its [breaking change
detection](https://buf.build/docs/cli/quickstart/#detect-breaking-changes).

```
buf breaking --against ".git#subdir=proto"
```

## Build

The build is [configured in `buf.gen.yaml`](https://buf.build/docs/generate/overview/).

```
buf generate
```