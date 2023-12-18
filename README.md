# Dummy attester as a Gramine enclave

The enclave itself only interacts on `stdin`/`stdout`.
It runs in a loop, expecting to receive a 128 byte message on `stdin`,
and producing a quote in response.
It therefore has an extremely simple interface.

To make it more practical, this also comes with a socket server
`dummyattester/server.py`. This runs on the same docker container, but outside
the enclave. In fact it invokes the gramine process, thus having access to its
`stdin`/`stout`. For convenience, there is also a `flask` server that runs
side-by-side and forwards requests to the relevant containers.

The docker environment can be built in either EPID or DCAP mode.

## Build the enclave (no SGX needed)

```shell
docker compose build
docker compose run --rm dummyattester
docker compose run --rm dummyattester-dcap
```

This builds and prints the MRENCLAVE.

## Use a web service to fetch a dummy attestation and check it

While best effort lasts, this is a server that returns dummy attestations on
arbitrary report data.

```shell
docker compose run --rm dummyattester bash -c " \
  curl -sS http://dummyattest.ln.soc1024.com/9113b0be77ed5d0d68680ec77206b8d587ed40679b71321ccdd5405e4d54a6820000000000000000000000000000000000000000000000000000000000000000 \
  | bash ../scripts/fetchandverify.sh \
"
```

To see how this server works look at `flaskserver.py` and `dummyattester/server.py`.

## Verify the report (untrusted, this could be done in RAVE)

From within the docker container:

```shell
gramine-sgx-ias-verify-report -E 000000000000000000000000000000000000 -v -r datareport -s datareportsig --allow-outdated-tcb
```

## Run the enclave in SGX

This command will run the enclave once and output a json object containing a quote

```shell
docker compose \
    --file docker-compose-sgx.yml \
  build \
    --build-arg RA_CLIENT_SPID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

RA_API_KEY=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy \
docker compose -f docker-compose-sgx.yml up --detach

curl -isS http://127.0.0.1:8000/9113b0be77ed5d0d68680ec77206b8d587ed40679b71321ccdd5405e4d54a6820000000000000000000000000000000000000000000000000000000000000000

curl -isS http://127.0.0.1:8000/forge-epid/9113b0be77ed5d0d68680ec77206b8d587ed40679b71321ccdd5405e4d54a6820000000000000000000000000000000000000000000000000000000000000000

curl -isS http://127.0.0.1:8000/dcap/9113b0be77ed5d0d68680ec77206b8d587ed40679b71321ccdd5405e4d54a6820000000000000000000000000000000000000000000000000000000000000000
```

>
> **Note:**
>
> Get your `RA_CLIENT_SPID` and `RA_API_KEY` from:
>
>   - https://api.portal.trustedservices.intel.com/developer-profile
>

## Complete the EPID attestation (untrusted)

```shell
gramine-sgx-ias-request report -k $RA_API_KEY -q quote -r datareport -s datareportsig
```
