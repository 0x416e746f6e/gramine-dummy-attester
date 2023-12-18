ARG GRAMINE_IMG_TAG=dcap-595ba4d

# ------------------------------------------------------------------------------

FROM ghcr.io/initc3/gramine:${GRAMINE_IMG_TAG}

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/app/.venvs/gramine

RUN apt-get update && \
    apt-get install --yes \
        jq \
        netcat \
        npm \
        python3-venv \
        software-properties-common
RUN python3.9 -m venv $VENV_PATH

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/

# Option A: Installing python dependencies from requirements.txt
# Compilation to .pyc is not reproducible. So we don't do this in the enclave.
COPY requirements.txt requirements.txt
RUN $VENV_PATH/bin/pip install --no-compile -r requirements.txt

ARG RA_TYPE=epid
ENV RA_TYPE=$RA_TYPE
ARG RA_CLIENT_SPID=51CAF5A48B450D624AEFE3286D314894
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG RA_CLIENT_LINKABLE=1
ENV RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE

ARG DEBUG=0
ENV DEBUG=$DEBUG
ARG SGX=1
ENV SGX=$SGX

WORKDIR /app/gramine-dummy-attester

ADD ./dummyattester/ ./dummyattester
ADD ./scripts ./scripts

WORKDIR /app/gramine-dummy-attester/dummyattester

RUN mkdir -p \
        input_data \
        output_data \
        enclave_data

RUN make \
        DEBUG=$DEBUG \
        RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE \
        RA_CLIENT_SPID=$RA_CLIENT_SPID \
        RA_TYPE=$RA_TYPE \
        SGX=$SGX

CMD [ "gramine-sgx-sigstruct-view", "python.sig" ]
