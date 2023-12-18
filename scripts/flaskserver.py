import base64
import json
import logging
import os
import socket
import tempfile
from binascii import hexlify
from subprocess import STDOUT, CalledProcessError, check_output

import eth_abi
from flask import Flask, Response

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

RA_CLIENT_SPID = os.environ['RA_CLIENT_SPID']
RA_API_KEY = os.environ['RA_API_KEY']
HOST_EPID=os.environ['HOST_EPID']
PORT_EPID=int(os.environ.get('PORT_EPID', 8000))
HOST_DCAP=os.environ['HOST_DCAP']
PORT_DCAP=int(os.environ.get('PORT_DCAP', 8000))

@app.route("/forge-epid/<userreportdata>")
def serverforge(userreportdata):
    logging.debug("serverforge: %s", userreportdata)

    assert len(userreportdata) == 128
    assert len(bytes.fromhex(userreportdata))==64

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_EPID, PORT_EPID))
        s.sendall(userreportdata.encode())

        f = s.makefile()
        quote = f.readline().strip()

    fpname = './testquote'
    with open(fpname,'wb') as fp:
    #with tempfile.NamedTemporaryFile() as fp:
        # fpname = fp.name
        fp.write(bytes.fromhex(quote))
        fp.flush()
        # Two more named files?
        try:
            cmd = f'gramine-sgx-ias-request report -g {RA_CLIENT_SPID} -k {RA_API_KEY} -q {fpname} -r ./datareport -s ./datareportsig -v'
            _ = check_output(cmd, shell=True, stderr=STDOUT)
        except CalledProcessError as e:
            res = f"exit code: {e.returncode}\n"
            if e.output:
                res += e.output.decode("utf-8")
            return res, 500

    datareport = open('./datareport').read()
    datareportsig = open('./datareportsig').read().strip()
    obj = dict(report=json.loads(datareport), reportsig=datareportsig)
    report = obj['report']
    items = (report['id'].encode(),
            report['timestamp'].encode(),
            str(report['version']).encode(),
            report['epidPseudonym'].encode(),
            report['advisoryURL'].encode(),
            json.dumps(report['advisoryIDs']).replace(' ', '').encode(),
            report['isvEnclaveQuoteStatus'].encode(),
            report['platformInfoBlob'].encode(),
            base64.b64decode(report['isvEnclaveQuoteBody']))
    abidata = eth_abi.encode(["bytes", "bytes", "bytes", "bytes", "bytes", "bytes", "bytes", "bytes", "bytes"], items)
    sig = base64.b64decode(obj['reportsig'])
    return Response(hexlify(eth_abi.encode(["bytes","bytes"], (abidata,sig))), mimetype='application/json')

@app.route("/dcap/<userreportdata>")
def serverdcap(userreportdata):
    logging.debug("serverdcap: %s", userreportdata)

    assert len(userreportdata) == 128
    assert len(bytes.fromhex(userreportdata))==64

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_DCAP, PORT_DCAP))
        s.sendall(userreportdata.encode())

        f = s.makefile()
        quote = f.readline().strip()

    fpname = './testquote'
    with open(fpname,'wb') as fp:
        fp.write(bytes.fromhex(quote))
        fp.flush()
        try:
            cmd = f'gramine-sgx-quote-view ./testquote'
            out = check_output(cmd, shell=True)
        except CalledProcessError as e:
            res = f"exit code: {e.returncode}\n"
            if e.output:
                res += e.output.decode("utf-8")
            return res, 500

    return Response(out + quote.encode(), mimetype='application/json')

@app.route("/<userreportdata>")
def server(userreportdata):
    logging.debug("server: %s", userreportdata)

    assert len(userreportdata) == 128
    assert len(bytes.fromhex(userreportdata))==64

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_EPID, PORT_EPID))
        s.sendall(userreportdata.encode())

        f = s.makefile()
        quote = f.readline().strip()

    fpname = './testquote'
    with open(fpname,'wb') as fp:
    #with tempfile.NamedTemporaryFile() as fp:
        # fpname = fp.name
        fp.write(bytes.fromhex(quote))
        fp.flush()
        # Two more named files?
        try:
            cmd = f'gramine-sgx-ias-request report -g {RA_CLIENT_SPID} -k {RA_API_KEY} -q {fpname} -r ./datareport -s ./datareportsig -v'
            _ = check_output(cmd, shell=True)
        except CalledProcessError as e:
            res = f"exit code: {e.returncode}\n"
            if e.output:
                res += e.output.decode("utf-8")
            return res, 500

    datareport = open('./datareport').read()
    datareportsig = open('./datareportsig').read().strip()
    obj = dict(report=json.loads(datareport), reportsig=datareportsig)

    return Response(json.dumps(obj).replace(' ',''), mimetype='application/json')
