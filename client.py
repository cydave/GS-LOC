#!/usr/bin/env python
# -*- coding: utf-8 -*-

import location_pb2
import urllib.request, urllib.error, urllib.parse
import random
import time
import argparse
import struct
import sys


SERVICE_URL = "https://{}.apple.com/clls/wloc"
SERVICE_SHOST = ["iphone-services", "gs-loc"]
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "locationd/1756.1.15 CFNetwork/711.5.6 Darwin/14.0.0",
}

URL = SERVICE_URL.format(SERVICE_SHOST[1])


class Header:
    def __init__(self):
        self.HEADER = self.__data()

    def __data(self):
        NUL_SQH = b"\x00\x01"  # NUL SOH      /* 0x0001 start of header */
        NUL_NUL = b"\x00\x00"  # NUL NUL      /* 0x0000 end of header */
        llength = b"\x00\x05"  # [length]     /* length of the locale string in bytes */
        locale = b"\x65\x6E\x5F\x55\x53"  # [locale]     /* en_US */
        ilength = (
            b"\x00\x13"  # [length]     /* length of the identifier string in bytes */
        )
        identifier = b"\x63\x6F\x6D\x2E\x61\x70\x70\x6c\x65\x2e\x6c\x6f\x63\x61\x74\x69\x6f\x6e\x64"  # [identifier] /* com.apple.locationd */
        vlength = b"\x00\x0c"  # [length]     /* length of the version string in bytes
        version = b"\x38\x2e\x34\x2e\x31\x2e\x31\x32\x48\x33\x32\x31"  # [version]    /* 8.4.1.12H321 ie. ios version and build */

        return (
            NUL_SQH
            + llength
            + locale
            + ilength
            + identifier
            + vlength
            + version
            + NUL_NUL
            + NUL_SQH
            + NUL_NUL
        )


header = Header().HEADER


def query(URL, DATA, HEADERS):

    req = urllib.request.Request(URL, DATA)

    req.add_header("User-Agent", HEADERS["User-Agent"])
    req.add_header("Content-type", HEADERS["Content-Type"])

    # req.add_header("Accept","*/*")
    # req.add_header("Accept-Language","en-us")
    # req.add_header("Accept-Encoding","gzip, deflate")
    # req.add_header("Accept-Charset","utf-8")

    handle = urllib.request.urlopen(req)
    data = handle.read()
    data_buffer = data[
        (data.find(b"\x00\x00\x00\x01\x00\x00") + 8) :
    ]  # +2 bc of the size bytes

    return data_buffer, data


def reqpay(macs, noise=0, signal=100):

    Request = location_pb2.Request()
    Request.noise = noise
    Request.signal = signal
    for MAC in macs:
        Request.wifis.add(mac=MAC)

    message = Request.SerializeToString()
    size = struct.pack(">h", len(message))  # big-endian Signed Short (16bit)
    return header + size + message


def resread(Buffer, KML):

    Response = location_pb2.Response()
    Response.ParseFromString(Buffer)

    narray = []

    for Wifi in Response.wifis:
        if Wifi.location.latitude != 18446744055709551616:
            mac = Wifi.mac
            print(("BSID MAC: %s" % mac))
            channel = Wifi.channel

            lat = int(Wifi.location.latitude) * pow(10, -8)
            lng = int(Wifi.location.longitude) * pow(10, -8)
            accuracy = Wifi.location.accuracy
            altitude = Wifi.location.altitude

            print(("\tLatitude: %s" % str(lat)))
            print(("\tLongitude: %s" % str(lng)))
            print(("\tAccuracy Radius: %s" % accuracy))
            print(("\tAltitude: %s" % altitude))

            if Wifi.location.HasField("altitudeAccuracy"):
                print(("\tAltitude Accuracy: %s" % Wifi.location.altitudeAccuracy))

            print(("Channel: %s\n\n" % channel))

            if KML == True:
                narray.append([mac, lat, lng])
        else:
            print(("%s Not Found" % Wifi.mac))
            narray.append([Wifi.mac, "Not Found", "Not Found"])

    if KML == True:
        with open("KML.kml", "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write("<Document>\n")
            for array in narray:
                f.write("\t<Placemark>\n")
                f.write("\t\t<description>" + str(array[0]) + "</description>\n")
                f.write("\t\t<Point>\n")
                f.write(
                    "\t\t\t<coordinates>"
                    + str(array[2])
                    + ","
                    + str(array[1])
                    + "</coordinates>\n"
                )
                f.write("\t\t</Point>\n")
                f.write("\t</Placemark>\n")
            f.write("</Document>\n")
            f.write("</kml>\n")

    return narray


def dbcall(macs, noise, signal, save, KML):
    DATA = reqpay(macs, 0, 100)

    Buffer = query(URL, DATA, HEADERS)[0]
    out = resread(Buffer, KML)

    if save:
        with open("buffer.bin", "wb") as f:
            f.write(Buffer)

    return out


def banner():

    print("   ________  _________         .____    ________  _________    ")
    print("  /  _____/ /   _____/         |    |   \_____  \ \_   ___ \   ")
    print(" /   \  ___ \_____  \   ______ |    |    /   |   \/    \  \/   ")
    print(" \    \_\  \/        \ /_____/ |    |___/    |    \     \____  ")
    print("  \______  /_______  /         |_______ \_______  /\______  /  ")
    print("         \/        \/                  \/       \/        \/   ")

    print("\n github.com/zadewg/GS-LOC/ :: Ofensive Intelligence Gathering")
    print("\n Apple Geolocation Services RE. Database Scraper     \n\n\n\n")


if __name__ == "__main__":
    banner()
    out = dbcall([str(sys.argv[1])], 0, 100, False, True)

    print(
        (
            "Mac {} {}".format(
                sys.argv[1],
                "Latitude: {}, Longitude:{}".format(str(out[0][1]), str(out[0][2])),
            )
        )
    )
