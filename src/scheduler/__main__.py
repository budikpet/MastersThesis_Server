from sys import argv
import scheduler.clock as clock
import scheduler.worker as worker

# This code is run when "python -m scheduler" is invoked. Not run when "scheduler" entry_point is used

if len(argv) == 2:
	command: str = argv[1]

	if command == 'clock':
		clock.main()
	elif command == 'worker':
		worker.main()
else:
	print("Usage: python -m scheduler clock|worker")