import sys
import argparse
import subprocess
import json
import tempfile
import os



def parse_cmd():
    try:
        parser_cmd = argparse.ArgumentParser()
        parser_cmd.add_argument("--name", type=str, required=True)
        parser_cmd.add_argument("--filename", type=str, required=True)
        parser_cmd.add_argument("--output", type=str, required=True)
        return parser_cmd.parse_args()
    except:
        print("Error")
        return -1


def blktest():
    iodepth = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    cmd_args = parse_cmd()
    print(cmd_args)
    name = cmd_args.name
    filename = cmd_args.filename
    output = cmd_args.output
    resalt_read = {}
    resalt_write = {}
    for io in iodepth:
        try:
            fio_res_read = fio_test(name, filename, str(io), 'randread', output)
            fio_res_write = fio_test(name, filename, str(io), 'randwrite', output)
            resalt_read[io] = fio_res_read["jobs"][0]["read"]["clat_ns"]["mean"]
            resalt_write[io] = fio_res_write["jobs"][0]["write"]["clat_ns"]["mean"]
        except subprocess.CalledProcessError as error:
            print(f"Error executing fio: {error}")
            print(f"Output: {error.output.decode()}")

def fio_test(name, filename, iodepth, operation, output):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.fio') as temp_fio_file:
        temp_fio_file.write(f"[{name}]\n".encode())
        temp_fio_file.write(f"iodepth={iodepth}\n".encode())
        temp_fio_file.write(f"rw={operation}\n".encode())
        temp_fio_file.write(b"ioengine=libaio\n")
        temp_fio_file.write(b"direct=1\n")
        temp_fio_file.write(b"bs=4k\n")
        temp_fio_file.write(b"size=1G\n")
        temp_fio_file.write(b"numjobs=1\n")
        temp_fio_file.write(b"runtime=1s\n")
        temp_fio_file.write(b"time_based\n")
        temp_fio_file.write(f"filename={filename}\n".encode())
        temp_fio_file.close()

        fio_command = [
            'fio',
            temp_fio_file.name,
            '--output-format', 'json'
        ]
        fio_command_start = subprocess.Popen(fio_command, stdout=subprocess.PIPE)
        try:
            line_output_of_test = fio_command_start.stdout.readline().decode('utf-8')
            output_of_test = line_output_of_test
            while line_output_of_test:
                line_output_of_test = fio_command_start.stdout.readline().decode('utf-8')
                output_of_test += line_output_of_test
            return json.loads(output_of_test)
        except subprocess.CalledProcessError as error:
            print(f"Command '{' '.join(fio_command)}' failed with exit code {error.returncode}")
            print(f"Output: {error.output.decode()}")
            raise
        finally:
            os.remove(temp_fio_file.name)
    return -1

if __name__ == "__main__":
    sys.exit(blktest())

