# Schema validation notes

Early on, I thought that records would come in DataCite 4.3 format. However, it turns out that InvenioRDM does not use DataCite record format per se; it uses something _compatible_ with DataCite. The upshot is that doing schema validation using DataCite schemas doesn't help, and in addition, it's not clear exactly what schema version is used in any given InvenioRDM installation. So, the current version of IGA doesn't do JSON schema validation. The code I started to write is in this directory, in case it's ever useful in the future.
