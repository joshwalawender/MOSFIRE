##-------------------------------------------------------------------------
## Import KTL python
##-------------------------------------------------------------------------
# Wrap ktl import in try/except so that we can maintain test case or
# simulator version of functions on machines without KTL installed.

def connect_to_ktl(serviceNames, noactions=False):
    if noactions is True:
        ktl = None
    else:
        try:
            import ktl
            from ktl import Exceptions as ktlExceptions
        except ModuleNotFoundError:
            ktl = None

    # Connect to KTL Services
    services = {}
    if ktl is not None:
        for service in serviceNames:
            try:
                services[service] = ktl.Service(service)
            except ktlExceptions.ktlError:
                log.error(f"Failed to connect to service {service}")

        assert len(serviceNames) == len(services.keys())
    return services
