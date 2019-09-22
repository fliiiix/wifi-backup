#!/usr/bin/env python

import dbus
import uuid
import json


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


    wsecurity = dbus.Dictionary({ 'key-mgmt': 'None' })
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


if __name__ == "__main__":
    filename = "wifi-connections.json"

    bus = dbus.SystemBus()
    proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings")
    settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")

    with open(filename, "r") as f:
        for json_con in f:
            jcon = json.loads(json_con)

            con = create_wifi_connection_dict(jcon)
            settings.AddConnection(con)