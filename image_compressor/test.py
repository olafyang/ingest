import os

testdir = "__test__"
testout = "__testout__"

def setup():
    os.mkdir(testdir)
    os.mkdir(testout)
    print(f"Created testing directory {testdir}")
    os.system(
        f"curl -o {testdir}/test.png https://ipque-cdn-main.s3.eu-central-003.backblazeb2.com/compress_test.png")
    print("Downloaded test file to testing directory")


def remove_test():
    os.system(f"rm -rf {testdir}")
    os.system(f"rm -rf {testout}")
    print("Removing testing directory")


def run_tests():
    print("Start running test")

    print("Testing defaults")
    os.system(f"python3 compressor.py {testdir}/test.png")

    print("Testing quality change")
    os.system(f"python3 compressor.py -q 50 {testdir}/test.png")

    print("Testing quality and size change")
    os.system(f"python3 compressor.py -q 50 -x 1000 {testdir}/test.png")

    print("Testing size change")
    os.system(f"python3 compressor.py -x 1000 {testdir}/test.png")

    print("Testing format and size change")
    os.system(f"python3 compressor.py -t png -x 1000 {testdir}/test.png")

    print("Testing S3 upload")
    os.system(f"python3 compressor.py -t png -x 1000 -u ipque-test {testdir}/test.png")

    print("Testing local output")
    os.system(f"python3 compressor.py -t png -x 1000 -o {testout} {testdir}/test.png")


if __name__ == "__main__":
    remove_test()
    setup()
    run_tests()
    remove_test()

    print("Success!")
