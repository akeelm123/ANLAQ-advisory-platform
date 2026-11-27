# Start the ANLAQ TCI synthetic local pilot — v0.9.2-alpha.1
The project owner selected Option A (local machine). This is a persistent synthetic candidate, not operational approval for real-client records.

## First launch on the owner's Mac
1. Open the executable start-local-pilot.command from Finder. It uses the existing bundled Python runtime when available, or Python 3 with requirements installed, and resolves the pinned methodology files in the current workspace or repository.
2. Confirm creation of a fictional-only vault. The launcher creates a new owner-only local data directory under Library/Application Support/ANLAQ-TCI-Synthetic unless TCI_LOCAL_DATA_DIR is set. Never place it in a Git checkout or synced folder. Do not choose real-client records.
3. At the terminal prompts, choose a unique vault passphrase (at least 16 characters), four distinct named user accounts (contributor, assessor, reviewer, owner) and four unique passwords (at least 12 characters). Secrets are prompted without echo; use an approved password manager/custody arrangement. Do not paste secrets into a chat or GitHub. Independent roles must be separate humans for actual review; these accounts alone cannot prove human independence.
4. The browser opens the actual local TCI address printed in the terminal (normally http://127.0.0.1:8765; if occupied, the launcher automatically selects an unused loopback port without stopping the other service). Sign in with your named account. Keep the terminal window open; Ctrl+C to stop. Do not reuse a previously saved localhost link if a different port was selected.
5. Next launch unlocks the existing vault with the same passphrase and requires a fresh named account login. There is no automatic account or vault reset. The owner can revoke other assessment memberships; re-enrolment, password reset and adding users require a future authorised administrative workflow.

No vault or real user credentials have been created by the development tests. The test screenshots show generated fictional accounts only.

## Backup and restore
The current image is checkpointed after each successful non-session POST; a sealed image is written and synced before atomic replacement. If a checkpoint fails, operations are refused until restart; inspect the last durable state before retrying. The test limit is 32 MiB database image and a rolling 30-day maximum archive expiry. This does not implement approved retention/deletion, external audit anchoring, or protection against an authorised owner deliberately substituting an older valid archive.

For maintenance, stop the running instance (exclusive lock). From this folder with the same Python runtime and pinned methodology variables, run:
```sh
python local_pilot.py --confirm-synthetic --data-dir "/approved/local/vault" --backup "/approved/offline/backup-new.tci"
```
Retain the original owner-only salt.bin file with the approved backup custody process; it is not itself the passphrase. Keep the secret separately and do not sync to public/cloud storage. Archive write refuses overwrite. Recovery into a NEW empty vault:
```sh
python local_pilot.py --confirm-synthetic --data-dir "/approved/local/recovered-vault" --restore-backup "/approved/offline/backup-new.tci" --restore-salt "/approved/offline/salt.bin" --open-browser
```
Use the original vault passphrase; recovery verifies archive authentication, validity, source hashes and audit, then seals a fresh checkpoint. Never overwrite the existing vault. Verify all recovered records independently before replacing any working procedure. Expired archives refuse restore, not deletion. Loss of the passphrase or salt prevents recovery. Do not use a recovered branch of history concurrently with the original; operational rollback protection/backup lifecycle still open.

## Before operational use
Verify FileVault/volume encryption, supported OS, screen lock, separate named OS accounts and physical access, secure local storage and backup custody, malware scanning/parser isolation, retention/deletion, independent audit/restore exercise, score calibration and synthetic cohort UAT. No LAN or remote access, no external model or scoring in local persistent mode, no client input. The synthetic confirmation is an operator boundary, not an automatic classifier of uploaded content. No public deployment.
