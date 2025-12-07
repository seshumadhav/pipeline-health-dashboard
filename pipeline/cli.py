import argparse
from pipeline.dashboard import render_dashboard

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
        render_dashboard()

if __name__ == "__main__":
    main()
