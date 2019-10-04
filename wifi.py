#!/usr/bin/env python

import os
import click
import dbus
import uuid
import json


@click.group()
def cli():
    pass


@cli.command("backup", help="Backup all wifi connections from NetworkManager.")
@click.argument('filename', required=False)
def backup(filename):
    if not filename:
        filename = "wifi-connections.json"

    cons = list_connections()
    write_to_file(cons, filename)

    print(f"[INFO] Wifi connections backuped to: {filename}")


@cli.command("import", help="Import wifi connections form a file to the NetworkManager.")
@click.argument('filename', required=False)
def _import(filename):
    if not filename:
        filename = "wifi-connections.json"

    print(f"[INFO] Wifi connections importing from: {filename}")
    if not os.path.isfile(filename):
        print(f"[ERROR] {filename} does not exist")
        return

    with open(filename, "r") as f:
        for json_con in f:
            jcon = json.loads(json_con)

            con = create_wifi_connection_dict(jcon)
            add_connection(con)


def add_connection(connection):
    bus = dbus.SystemBus()
    service_name = "org.freedesktop.NetworkManager"
    proxy = bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
    settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
    settings.AddConnection(connection)


def create_wifi_connection_dict(connection):
    name = connection['name']
    ssid = connection['ssid'].encode("utf-8")
    secret_type = connection['secret-type']

    connection_type = dbus.Dictionary({
        'type': '802-11-wireless',
        'uuid': str(uuid.uuid4()),
        'id': name})

    wifi = dbus.Dictionary({
        'ssid': dbus.ByteArray(ssid),
        'mode': 'infrastructure',
    })

    wsecurity = dbus.Dictionary({'key-mgmt': 'None'})
    if secret_type == "wpa-psk":
        psk = connection['secrets']['psk']

        wsecurity = dbus.Dictionary({
            'key-mgmt': 'wpa-psk',
            'auth-alg': 'open',
            'psk': psk,
        })
    if secret_type == "wpa-eap":
        secrets = connection['secrets']

        wsecurity = dbus.Dictionary({
            'key-mgmt': 'wpa-eap',
            'auth-alg': 'open',
        })

        wsecurity_enterprise = dbus.Dictionary({
            'eap': [secrets['eap']],
            'identity': secrets['identity'],
            'phase2-auth': secrets['phase2-auth'],
            'password': secrets['password']
        })

        if secrets['anonymous-identity']:
            wsecurity_enterprise['anonymous-identity'] = secrets['anonymous-identity']

    ip_settings = dbus.Dictionary({'method': 'auto'})
    con = dbus.Dictionary({
        'connection': connection_type,
        '802-11-wireless': wifi,
        '802-11-wireless-security': wsecurity,
        'ipv4': ip_settings,
        'ipv6': ip_settings
    })

    if secret_type == "wpa-eap":
        con['802-1x'] = wsecurity_enterprise

    return con


def merge_secrets(proxy, config, setting_name):
    try:
        # returns a dict of dicts mapping name::setting,
        # where setting is a dict mapping key::value.
        # Each member of the 'setting' dict is a secret
        secrets = proxy.GetSecrets(setting_name)

        # Copy the secrets into our connection config
        for setting in secrets:
            for key in secrets[setting]:
                config[setting_name][key] = secrets[setting][key]
    except Exception as e:
        pass


def list_connections():
    connections = list()
    bus = dbus.SystemBus()
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


if __name__ == '__main__':
    cli()
