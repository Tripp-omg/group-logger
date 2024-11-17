import multiprocessing
import subprocess

def run_bot(script_path):
    print(f"Running {script_path}...")
    process = subprocess.Popen(['python', script_path])
    process.communicate()
    print(f"Finished running {script_path}.")

if __name__ == "__main__":
    # Paths to the bot scripts
    scripts = ['publish/Goti.py', 'publish/Main.py']

    # Create and start processes for each script
    processes = []
    for script in scripts:
        process = multiprocessing.Process(target=run_bot, args=(script,))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

    print("All bots are running.")