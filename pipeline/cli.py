import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="pipeline-health-dashboard",
        description="Prototype pipeline health dashboard"
    )
    parser.add_argument(
        "command",
        choices=["run"],
        help="Run the dashboard"
    )

    args = parser.parse_args()

    if args.command == "run":
        print("Pipeline Health Dashboard")

if __name__ == "__main__":
    main()
