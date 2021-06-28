# Home Assistant Registry Cleaner

## Requirements

1. The entity must be disabled
2. User running script must have write access to all of the core files (sudo is your friend)
3. Must provide full path to Home Assistant configuration directory
4. Python3 required

## Example

1. Remove Entity

```` console
sudo python3 harc.py /path/to/hass/config sensor.senor_entity_id
````

## Disclamier

Use at your own risk. If possible, run on non-production first.
