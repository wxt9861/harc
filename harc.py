import argparse
import sys
import json


def main():
    if sys.version_info.major < 3:
        sys.exit("Python 3 requiried")

    arg_parser = create_arg_parser()
    parsed_args = arg_parser.parse_args(sys.argv[1:])
    path = parsed_args.configDirectory
    targetEntityId = parsed_args.targetEntityId

    # files needed for this script within Home Assistant folder
    # where these files are normally stored
    files = [
        "core.config_entries",
        "core.device_registry",
        "core.entity_registry",
        "core.restore_state",
    ]
    configList = read_file(files[0], path)
    deviceList = read_file(files[1], path)
    entityList = read_file(files[2], path)
    restoreList = read_file(files[3], path)

    # print total number of keys found in each file
    get_totals(files, configList, deviceList, entityList, restoreList)

    # show items for selected args
    if parsed_args.show_entries:
        print("configList Entries")
        c = 0
        for key in configList["data"]["entries"]:
            print(
                "{:03d}".format(c),
                ":",
                key["title"],
                "-",
                key["domain"],
                "-",
                key["entry_id"],
            )
            c += 1

    if parsed_args.show_devices:
        print("deviceLists:")
        d = 0
        for key in deviceList["data"]["deviceLists"]:
            print("{:03d}".format(d), ":", key["id"])
            d += 1

    if parsed_args.show_entities:
        print("Entities:")
        e = 0
        for key in entityList["data"]["entities"]:
            print("{:03d}".format(e), ":", key["entity_id"])
            e += 1

    print("Looking for", targetEntityId)

    # check if targetEntity exists
    if targetEntityId in [key["entity_id"] for key in entityList["data"]["entities"]]:
        # start - scan entity list, find info on entity we need, remove it
        entityRemoved = False
        deviceRemoved = False
        restoreStateRemove = False
        entityLastSeen = "N/A"

        e = 0
        for key in entityList["data"]["entities"]:
            if key["entity_id"] == targetEntityId:
                if key["disabled_by"] is None:
                    status = "Enabled"
                else:
                    status = "Disabled"

                entityId = key["unique_id"]
                deviceId = key["device_id"]
                configId = key["config_entry_id"]
                for item in restoreList["data"]:
                    if item["state"]["entity_id"] == key["entity_id"]:
                        entityLastSeen = (item["last_seen"])

                print(
                    "entity ID:", key["entity_id"],
                    "- Status:", status,
                    "- Last Seen:", entityLastSeen)
                print("device ID:", key["device_id"])
                print("config Entry ID:", key["config_entry_id"])

                # check for other entities share the same deviceList and configList IDs
                print("\nOther devices related to this entity's device")
                numRelatedDevices = 0
                for key in entityList["data"]["entities"]:
                    if key["device_id"] == deviceId:
                        print(key["entity_id"])
                        numRelatedDevices += 1

                print("\nOther entities related to this entity's Config Entry")
                numRelatedConfig = 0
                deviceCount = 0
                for key in entityList["data"]["entities"]:
                    if key["config_entry_id"] == configId:
                        print(key["entity_id"])
                        numRelatedConfig += 1
                    deviceCount += 1

                # Confirm and remove from entityList, oherwie skip
                # at this point, nothing is written to the file, that step is next
                removeQuestion = "\nRemove entity " + targetEntityId + " ?"
                if query_yes_no(removeQuestion, "no") is True:
                    # these will be used to determine if file commit is needed

                    if status == "Disabled":
                        print("Removing entity", targetEntityId)
                        if entityList["data"]["entities"].pop(e):
                            entityRemoved = True

                        # remove from deviceList
                        d = 0
                        for key in deviceList["data"]["devices"]:
                            if (
                                key["id"] == deviceId
                                and key["identifiers"][0][1] == entityId
                            ):
                                print("Removing device", deviceId)
                                if deviceList["data"]["devices"].pop(d):
                                    deviceRemoved = True
                            d += 1

                        # remove from restoreList
                        r = 0
                        for item in restoreList["data"]:
                            if(item["state"]["entity_id"] == targetEntityId):
                                print("Removing restore state")
                                if restoreList["data"].pop(r):
                                    restoreStateRemove = True
                            r += 1
                    else:
                        print(
                            "Entity is not disabled. "
                            "Entity must be disabled before it can be removed"
                        )

            e += 1
        # end - scan entity list, find info on entity we need, remove it

        # print total number of keys found in each file after changes
        get_totals(files, configList, deviceList, entityList, restoreList)

        # if changes were made, ask to comomit to file
        if entityRemoved is True:
            commitQuestion = "\nCommit Changes to file?"
            if query_yes_no(commitQuestion, "no") is True:
                write_file(entityList, files[2], path)
                if numRelatedConfig == 1:
                    write_file(configList, files[0], path)
                if deviceRemoved is True:
                    write_file(deviceList, files[1], path)
                if restoreStateRemove is True:
                    write_file(restoreList, files[3], path)
    else:
        print("Entity", targetEntityId, "not found")


# check files and assign files
def read_file(file, path, coreStorage="/.storage/"):
    """Open files and import data."""

    fullPath = path + coreStorage + file

    try:
        configFile = open(fullPath, "r+")
        print("Found", configFile.name)
    except FileNotFoundError as e:
        sys.exit("config file not found", e.filename)
    except PermissionError as e:
        # sys.exit("Permission denied: " + e.filename)
        # try opoening in read only mode if not able to open for write
        # this will not allow any changes, but can be used to browse entries, etc
        try:
            configFile = open(fullPath, "r")
            print("READ ONLY - Found", e.filename)
            loadJson = json.load(configFile)
            configFile.close()
            return loadJson
        except PermissionError as e:
            sys.exit("Permission denied: " + e.filename)
    else:
        loadJson = json.load(configFile)
        configFile.close()
        return loadJson


def write_file(data, file, path, coreStorage="/.storage/"):
    """Write to file once ready to commit changes."""

    fullPath = path + coreStorage + file

    try:
        with open(fullPath, "w") as filetowrite:
            json.dump(data, filetowrite, indent=4)
    except PermissionError as e:
        sys.exit("Permission denied: " + e.filename)


def get_totals(files, *kwargs):
    """Calculate total entries for each file."""
    configList = kwargs[0]
    deviceList = kwargs[1]
    entityList = kwargs[2]
    restoreList = kwargs[3]
    print()
    print(files[0], ":", len(configList["data"]["entries"]))
    print(files[1], ":", len(deviceList["data"]["devices"]))
    print(files[2], ":", len(entityList["data"]["entities"]))
    print(files[3], ":", len(restoreList["data"]))
    print()


def create_arg_parser():
    """Create parser for command line arguments."""

    parser = argparse.ArgumentParser(
        description="Python Script to remove unwanted entities",
        prog="Home Assistant Registry Cleaner",
    )
    parser.add_argument(
        "configDirectory", help="Home Assistant config directory"
    )
    parser.add_argument("targetEntityId", help="Name of the entityList ID to remove")
    parser.add_argument(
        "--show-devices",
        action="store_true",
        help="List devices from core.device_registry",
    )
    parser.add_argument(
        "--show-entities",
        action="store_true",
        help="List entities from core.entity_registry",
    )
    parser.add_argument(
        "--show-entries",
        action="store_true",
        help="List config entries from core.config_entries",
    )

    return parser


def query_yes_no(question, default=None):
    """
    Ask a yes/no question to confirm data changes.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.

    The return value is True for "yes" or False for "no".
    """

    valid = {"yes": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = "[Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Respond with yes or no")


if __name__ == "__main__":
    main()
