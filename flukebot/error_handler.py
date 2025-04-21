import sys
import traceback

def cleanup():
    print("🧹 Running cleanup before shutdown...")
    # client.close()


# For uncaught exceptions in synchronous code (main thread)
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print("\n❌ Unhandled Exception:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    cleanup()


# Set the global exception handler
sys.excepthook = handle_exception
