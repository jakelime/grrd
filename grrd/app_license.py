import re
import subprocess
import platform

# local libraries
if __name__.startswith("gaia"):
    from .config import Config
    from .utils import timer

else:
    from config import Config
    from utils import timer


class LicenseManager:
    descriptor1: str="NOT ACTIVATED"
    descriptor2: str=""

    def __init__(self, log, cfg):
        self.log = log
        self.cfg = cfg
        self.current_os = platform.system()
        self.domains = [".office.amsiag.com", ".int.osram-light.com"]
        self.refresh_license()

    @staticmethod
    def get_certificates(os: str, check: bool = False, timeout: int = 2):
        if os.lower() == "darwin":
            certutil = subprocess.run(
                ["security", "find-certificate", "-a"],
                check=check,
                timeout=timeout,
                capture_output=True,
                encoding="utf-8",
            )

        elif os.lower() == "windows":
            certutil = subprocess.run(
                ["certutil", "-dump"],
                check=check,
                timeout=timeout,
                capture_output=True,
                encoding="utf-8",
            )

        else:
            raise NotImplementedError

        return certutil.stdout

    def has_ams_osram_cert_server(self, cert_str, domains):
        try:
            for domain in domains:
                m = re.search(f"{domain}", cert_str)
                if m:
                    self.descriptor2 = m.group(0)
                    try:
                        self.descriptor2 = ".".join(self.descriptor2.split(".")[-2:])
                    except Exception:
                        pass
                    self.log.debug(f"found cert provided by {self.descriptor2}")
                    return True
            return False

        except Exception as e:
            self.log.error(f"{e=}")
            return False

    def refresh_license(self):
        try:
            cert_str = self.get_certificates(self.current_os)
            self.licensed = self.has_ams_osram_cert_server(cert_str, self.domains)
            self.descriptor1 = "Corporate license"

        except FileNotFoundError as e:
            log.error(f"process fail because the OS's certutil is not available\n{e}")
        except subprocess.CalledProcessError as e:
            log.error("process failed because did not return a successful return code")
            log.error(f"returned {e.returncode}\n{e}")
        except subprocess.TimeoutExpired as e:
            log.error(f"process timed out.\n{e}")


@timer
def main():
    global log, cfg
    license_manager = LicenseManager(log, cfg)
    log.info(f"{license_manager.licensed=}")


if __name__ == "__main__":
    import logging
    c = Config("msag", hard_reset=True, default_loglevel=logging.DEBUG)
    log = c.log
    cfg = c.cfg
    main()
