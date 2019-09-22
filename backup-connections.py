#!/usr/bin/env python

import dbus
import json

bus = dbus.SystemBus()

def merge_secrets(proxy, config, setting_name):
    try:
        # returns a dict of dicts mapping name::setting, where setting is a dict
        # mapping key::value.  Each member of the 'setting' dict is a secret
        secrets = proxy.GetSecrets(setting_name)

        # Copy the secrets into our connection config
        for setting in secrets:
            for key in secrets[setting]:
                config[setting_name][key] = secrets[setting][key]
    except Exception as e:
        pass


def list_connections():
    connections = list()
    service_name = "org.freedesktop.NetworkManager"
    proxy = bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
    settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
    connection_paths = settings.ListConnections()

    for path in connection_paths:
        con_proxy = bus.get_object(service_name, path)
        settings_connection = dbus.Interface(con_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        config = settings_connection.GetSettings()

        merge_secrets(settings_connection, config, '802-11-wireless')
        merge_secrets(settings_connection, config, '802-11-wireless-security')
        merge_secrets(settings_connection, config, '802-1x')

        if (config['connection']['type'] == "802-11-wireless"):
            ssid = ''.join([chr(byte) for byte in config['802-11-wireless']['ssid']])
            
            sec_type = ""
            sec = {}
            if ('802-11-wireless-security' in config):
                sec_type = config['802-11-wireless-security']['key-mgmt']
                if (sec_type == "wpa-psk"):
                    sec = { 'psk': f"{config['802-11-wireless-security']['psk']}" }
                if (sec_type == "wpa-eap"):
                    print(config['802-1x'])
                    ano_identity = ""
                    if('anonymous-identity' in config['802-1x']):
                        ano_identity = f"{config['802-1x']['anonymous-identity']}"

                    sec = { 
                      'eap': f"{config['802-1x']['eap'][0]}",
                      'identity': f"{config['802-1x']['identity']}",
                      'anonymous-identity': ano_identity,
                      'phase2-auth': f"{config['802-1x']['phase2-auth']}",
                      'password': f"{config['802-1x']['password']}"
                    }

            con = { 
              'name': f"{config['connection']['id']}", 
              'ssid': ssid, 
              'secret-type': f"{sec_type}",
              'secrets': sec 
            }
            connections.append(con)

    return connections


def write_to_file(connections, filename):
    with open(filename, "w+") as f:
        for con in connections:
            f.write(f"{json.dumps(con)}\n")


if __name__ == "__main__":
    filename = "wifi-connections.json"

    cons = list_connections()
    write_to_file(cons, filename)

    print(f"Wifi connection backuped to: {filename}")