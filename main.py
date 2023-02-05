from src import bot
import sys
import discord
import os
from keep_alive import keep_alive
def check_verion() -> None:
    import pkg_resources
    import src.log

    # init loggger
    logger = src.log.setup_logger(__name__)

    # Read the requirements.txt file and add each line to a list
    with open('requirements.txt') as f:
        required = f.read().splitlines()

    # For each library listed in requirements.txt, check if the corresponding version is installed
    for package in required:
        # Use the pkg_resources library to get information about the installed version of the library
        package_name, package_verion = package.split('==')
        installed = pkg_resources.get_distribution(package_name)
        # Extract the library name and version number
        name, version = installed.project_name, installed.version
        # Compare the version number to see if it matches the one in requirements.txt
        if package != f'{name}=={version}':
            logger.error('%s version %s is installed but does not match the requirements',name,version)
            sys.exit();



keep_alive()
try:
    if __name__ == '__main__': 
        check_verion()
        bot.run_discord_bot()
except discord.errors.HTTPException:
    print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
    os.system('kill 1')
    os.system("python restarter.py")
