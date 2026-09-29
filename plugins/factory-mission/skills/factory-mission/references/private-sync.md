# Private overlay synchronization

Use `../scripts/sync_private.py` to keep a private user-level variant aligned
with the public skill without committing personal model IDs or policies.

The private overlay lives outside the public repository. Its `overlay.json`
uses schema version 1 and may define:

- `version_suffix`, such as `-private.1`;
- private frontmatter `metadata`;
- `text_operations`, each with a public file, one exact `after` anchor, and a
  private fragment file;
- `files` copied from the overlay into the resulting skill;
- `extra_evals`, a private JSON list appended to public behavioral cases.
- `extra_replays`, a private JSON list appended to deterministic replay cases.

Run a dry comparison first:

```text
python scripts/sync_private.py --source <public-skill> --target <private-skill> --overlay <private-overlay>
```

Exit `0` means aligned, `1` lists expected differences, and `2` reports an
invalid or unsafe sync. Apply reviewed changes with a backup:

```text
python scripts/sync_private.py --source <public-skill> --target <private-skill> --overlay <private-overlay> --apply --backup <backup-directory>
```

The first sync over an existing unmanaged target requires
`--adopt-existing` after reviewing the dry-run paths. Later syncs record hashes
in `.factory-mission-sync.json` and refuse to overwrite a managed file changed
since the previous sync. Move the intentional change into the public skill or
private overlay, then retry. The tool writes files atomically and removes only
previously managed files whose recorded hashes still match.

Validate the synchronized skill and run public plus private behavioral tests
before replacing an environment-level installation.
