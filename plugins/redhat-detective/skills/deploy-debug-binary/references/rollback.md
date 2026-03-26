# Rollback

Rollback is straightforward because the bind mount never touched the original binary.

## Quick Rollback

```bash
# Stop the service
ssh core@${WORKER} "sudo systemctl stop <service>"

# Unmount the bind mount (restores original binary)
ssh core@${WORKER} "sudo umount <original-path>"

# Remove any config drop-ins
ssh core@${WORKER} "sudo rm -f <config-drop-in-path>"

# Start the service (now using the original binary)
ssh core@${WORKER} "sudo systemctl start <service>"

# Restart dependent services
ssh core@${WORKER} "sudo systemctl restart <dependent-service>"

# Verify original version
ssh core@${WORKER} "sudo <binary> --version"
```

## Verify Node Health

```bash
oc get node <node>
```

Wait for `Ready` status. If the node doesn't recover, check service logs:

```bash
ssh core@${WORKER} "sudo journalctl -u <service> --no-pager -n 30"
```

## Cleanup

The debug binary remains at `/home/core/<binary>` after unmounting. Remove it if no longer needed:

```bash
ssh core@${WORKER} "rm /home/core/<binary>"
```

## If the Service Won't Start After Rollback

This shouldn't happen since the original binary is untouched, but if it does:

1. Verify the unmount actually happened: `mount | grep <original-path>`
2. Check the original binary is intact: `rpm -V <package-name>`
3. Check SELinux: `sudo restorecon <original-path>`
4. Check logs: `sudo journalctl -u <service> -n 50`
