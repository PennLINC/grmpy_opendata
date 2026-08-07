# Recovering annex objects a CLI upload reported as failed

When `openneuro upload` finishes with `Failed to transfer annex object ... after N
attempts`, two separate things are wrong and both have to be fixed:

1. the object content was never stored on the remote, and
2. the git-annex location log records the object as **absent** (`0`), which
   `git-annex get` trusts — so the file is unfetchable even once the content
   exists.

Re-running the upload does **not** repair either one. `commitAnnexBranch()` skips
any key whose log already mentions the remote's UUID, including when it says
absent, so the stale marker survives every subsequent run.

Scripts referenced below are in `code/openneuro/recovery/`.

## 1. Which objects are actually missing?

```bash
bash verifyfailed.sh <upload log>
```

Extracts every failed key from the log and queries `<endpoint>/annex/<key>`.
`200` = present, `404` = genuinely missing. Reported failures are not reliable on
their own — of 66 reported for ds008606, 3 were already present.

## 2. Upload the missing objects

```bash
bash repairkeys.sh <upload log> <dataset dir> --dry-run   # resolve paths only
bash repairkeys.sh <upload log> <dataset dir>             # upload
```

Matches each key to a local file by size, verifies SHA256 against the hash in the
key, then POSTs it. Prints the real HTTP status per file, which `storeKey()` in
the CLI discards.

Expect `200` for missing objects and `409` for ones already present — 409 is the
server refusing to replace an existing object, i.e. success.

Re-run `verifyfailed.sh` afterwards; it should report `actually missing: 0`.

## 3. Check the location log

Content on the remote is not enough. Clone the dataset:

```bash
git clone https://github.com/openneuro/ds008606.git
cd ds008606 && git annex init && git annex enableremote openneuro
```

Check the location log:

```bash
bash annexstate.sh <clone dir> [key]
```

Look at the log entry for a repaired key:

```
1785998691s 0 57538107-c452-4407-bf8d-1fca76134852
             ^ 0 = absent, 1 = present
```

Compare against a key that uploaded cleanly, which should read `1`.

## 4. Correct the location log and push

```bash
bash fixlocationlog.sh <clone dir> <upload log>          # report
bash fixlocationlog.sh <clone dir> <upload log> --fix    # rewrite + push
```

Runs `git annex setpresentkey <key> <remote uuid> 1` for each repaired key and
pushes the `git-annex` branch. Only location metadata changes; `main` and file
content are untouched.

## 5. Confirm as a consumer would

```bash
cd <clone> && git annex get <one of the repaired files>
```

`ok` means the dataset is complete: content stored, location log accurate, and
reachable through the special remote.

A `BrokenPipe` traceback from the special-remote helper after `ok` is harmless -
it writes to stdout after git-annex closes the pipe.

## Worked example: ds008606

96,001 files / 192 GB, 81,510 annex keys.

| step | result |
|---|---|
| upload reported failures | 66 keys |
| `verifyfailed.sh` | 63 missing, 3 present |
| `repairkeys.sh` | 63 × HTTP 200, 3 × 409 |
| `verifyfailed.sh` (again) | 66/66 present |
| `fixlocationlog.sh` | 63 marked absent → set present, branch pushed |
| `git annex get` | `ok` |

The 63 failures were transient: every one succeeded on a single later attempt
from the same host and credentials. The CLI's three retries fire with no delay
between them, so a server hiccup lasting more than a second exhausts all three.
