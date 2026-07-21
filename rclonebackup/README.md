# Rclone Cloud Mount

Mounts a cloud storage remote (rclone-supported) into a read/write folder inside Home Assistant, so it can be used as a normal backup destination from Supervisor, automations or file explorer.

Primary target is an Azure Storage Account (Blob container), but any other rclone backend can be used through the `custom` provider option.

## How it works

On start, the add-on builds an `rclone.conf` from the options you set, then runs `rclone mount` in the foreground against `mount_path`. When the add-on stops, the mount is released cleanly.

## Options

| Option | Description |
|---|---|
| `storage_provider` | `azureblob` (default) or `custom` |
| `azure_account_name` | Storage account name |
| `azure_account_key` | Storage account access key |
| `azure_sas_url` | SAS URL, used instead of the access key if set |
| `azure_container` | Blob container name |
| `remote_subpath` | Optional subfolder inside the container |
| `mount_path` | Local path where the remote gets mounted, e.g. `/share/cloud` |
| `vfs_cache_mode` | rclone VFS cache mode: `off`, `minimal`, `writes`, `full` |
| `extra_rclone_config` | Full rclone remote definition, used only when `storage_provider` is `custom` |

When `azure_sas_url` is provided it takes priority over `azure_account_key`.

## Custom provider example

Set `storage_provider` to `custom` and fill `extra_rclone_config` with a full remote section, e.g. for OneDrive, Google Drive, S3, WebDAV, etc. It must define a remote named `remote`:

```
[remote]
type = onedrive
token = {"access_token":"...","token_type":"Bearer","refresh_token":"...","expiry":"..."}
```

## Notes

- Requires access to `/dev/fuse` and `SYS_ADMIN`, both already set in the add-on config.
- `mount_path` should point somewhere inside `/share`, `/backup` or `/media` so it stays reachable from Home Assistant.
- Because it's a FUSE mount, files written to `mount_path` are uploaded to the cloud remote as rclone flushes its cache.
