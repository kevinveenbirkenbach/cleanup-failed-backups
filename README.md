# Cleanup Failed Docker Backups
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach) [![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach) [![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)


This repository hosts a Bash script designed for cleaning up directories within the Docker Volume Backup system. It is intended to be used in conjunction with the [Docker Volume Backup](https://github.com/kevinveenbirkenbach/docker-volume-backup) project.

## Description

This script operates by traversing subdirectories within a specific main directory and, under certain conditions, proposes their deletion to the user. It is useful in managing backup directories, especially when certain directories can be cleaned up based on the absence of a particular subdirectory and the name of the directories themselves.

The script takes two arguments: a backup hash and a trigger directory. It constructs the main directory path using the given backup hash, and then iterates over all items within the main directory. If a directory's name matches a specific date-time-stamp pattern and lacks the specified trigger directory, the script will list its contents and ask for user confirmation to delete the directory.

For more detailed information about the script's workings, refer to the comments within the `cleanup.sh` script file.

## Usage

To use this script, clone this repository to your local system and run the script with the necessary arguments. The command should be structured as follows:

```bash
bash cleanup.sh BACKUP_HASH
```

Replace ```BACKUP_HASH``` and ```TRIGGER_DIRECTORY``` with your actual values.

## License
This project is licensed under the GNU Affero General Public License v3.0. See the LICENSE file for more information.

## Author
This script is developed by Kevin Veen-Birkenbach. You can reach out to him at kevin@veen.world or visit his website at https://www.veen.world.

## Created with Chat GPT
https://chat.openai.com/share/01222e15-8e1d-436d-b05b-29f406adb2ea
