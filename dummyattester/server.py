import logging
import socket
import subprocess
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

def server(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', 8000))):

    cmd = "gramine-sgx ./python"
    logging.info("Starting the SGX process: %s", cmd)
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logging.info("Server is listening on %s:%d", host, port)
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    logging.info("Connected by %s", addr)
                    while True:
                        data = conn.recv(128)
                        if not data: break

                        # Check hex conversion
                        data = data.decode('utf-8')
                        logging.info('Received data: %s', data)
                        assert len(bytes.fromhex(data)) == 64

                        exit_code = proc.poll()
                        if exit_code:
                            out = f"exit code: {exit_code}"
                            out += "stdout:\n" + proc.stdout.read().decode('utf-8') if proc.stdout else ""
                            out += "stderr:\n" + proc.stderr.read().decode('utf-8') if proc.stderr else ""
                            logging.error(
                                "SGX process had (already) terminated: %s",
                                out.strip(),
                            )

                            logging.info("Re-starting the SGX process: %s", cmd)
                            proc = subprocess.Popen(
                                cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                            )

                        # Write
                        logging.info('Writing proc input')
                        proc.stdin.write(data.encode()+b'\n')
                        proc.stdin.flush()

                        # Receive the quote
                        logging.info('Reading procs output')
                        proc.stdout.flush()
                        quote = proc.stdout.readline()

                        # Quote is in hex, still write it in hex
                        if quote:
                            logging.info("quote: %s", quote.decode('utf-8'))
                            conn.sendall(quote)
                        else:
                            logging.info("empty quote")
                            conn.sendall(b"\n")

            except Exception as e:
                print(f"An error occurred: {e}")
                continue

if __name__ == '__main__':
    server()
