import logging
from typing import List, Tuple

from dnslib import DNSRecord, textwrap
from dnslib.server import DNSLogger, DNSServer
from dnslib.zoneresolver import ZoneResolver


# DNS Server code in __init__ taken from dnslib examples with minor modifications

LOGGER = logging.getLogger(__name__)


class ACMEDNS:
    def __init__(self, zone: str = ""):
        LOGGER.debug(f"DNS Server received zones: \n {zone}")
        self.resolver = ZoneResolver(textwrap.dedent(zone))
        self.dns_logger = DNSLogger(prefix=False)
        self.server = DNSServer(
            self.resolver, port=10053, address="0.0.0.0", logger=self.dns_logger
        )

    def start(self):
        LOGGER.info("Starting DNS server...")
        self.server.start_thread()

    def stop(self):
        LOGGER.info("Stopping DNS server...")
        self.server.server.server_close()

    def update_zone(self, new_zone: str):
        LOGGER.debug(f"Updating DNS with new zone:\n {new_zone}")
        self.stop()
        self.resolver = ZoneResolver(textwrap.dedent(new_zone))
        self.server = DNSServer(
            self.resolver, port=10053, address="0.0.0.0", logger=self.dns_logger
        )
        self.start()


def build_dns_challenge_zones(domains: List[Tuple[str, str]],):
    zone = "\n".join(
        [
            f'_acme-challenge.{domain}. 300 TXT "{key_auth}"'
            for domain, key_auth in domains
        ]
    )
    return zone


def build_http_challenge_zones(domains: List[str], record: str):
    zone = "\n".join([f"{domain}. 60 A {record}" for domain in domains])
    return zone


def test():
    zone1 = build_http_challenge_zones(["abc.com", "test.com"], record="1.2.3.4")

    s = ACMEDNS(zone1)
    s.start()
    q = DNSRecord.question("abc.com", qtype="A")
    a = q.send("127.0.0.1", 10053)
    print(DNSRecord.parse(a))

    zone2 = build_dns_challenge_zones(
        [("abc.com", "TEST_TOKEN1"), ("test.com", "TEST_TOKEN2")]
    )
    s.update_zone(zone2)
    q = DNSRecord.question("abc.com", qtype="TXT")
    a = q.send("127.0.0.1", 10053)
    print(DNSRecord.parse(a))

    s.stop()


if __name__ == "__main__":
    test()
