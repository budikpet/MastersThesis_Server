from sys import argv
import automator.scheduler as scheduler
import automator.worker as worker

# This code is run when "python -m automator" is invoked. Not run when "automator" entry_point is used

if len(argv) == 2:
    command: str = argv[1]

    if command == 'scheduler':
        scheduler.main()
    elif command == 'worker':
        worker.main()
else:
    print("Usage: python -m automator [scheduler|worker]")
