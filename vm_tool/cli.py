import argparse

def main():
    parser = argparse.ArgumentParser(description='VM Tool version info')
    parser.add_argument('--version', action='version', version='1.0.28')
    parser.parse_args()

if __name__ == '__main__':
    main()