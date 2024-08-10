import time


class Timer:
    _last_time = None
    _results = []

    @classmethod
    def start(cls, description):
        """End the previous timer (if any) and start a new one with the given description."""
        if cls._last_time is not None:
            # Calculate the elapsed time for the previous timer
            elapsed_time_ns = time.process_time_ns() - cls._last_time
            elapsed_time_ms = elapsed_time_ns / 1_000_000  # Convert to milliseconds

            # Add the result to the list
            cls._results.append(f'"{cls._current_description}"={elapsed_time_ms:.2f}ms')

        # Start the new timer
        cls._current_description = description
        cls._last_time = time.process_time_ns()

    @classmethod
    def stop(cls, logger):
        """End the last timer and log all the results."""
        if cls._last_time is not None:
            # Calculate the elapsed time for the last timer
            elapsed_time_ns = time.process_time_ns() - cls._last_time
            elapsed_time_ms = elapsed_time_ns / 1_000_000  # Convert to milliseconds

            # Add the last result to the list
            cls._results.append(f'"{cls._current_description}"={elapsed_time_ms:.2f}ms')

        # Log all results
        logger.info(", ".join(cls._results))

        # Clear the state
        cls._last_time = None
        cls._results = []
