# Certificates directory

Private keys and issued certificates are **generated locally** and must **not** be committed to git.

| Folder   | Contents                          |
|----------|-----------------------------------|
| `ca/`    | Root CA cert/key (auto-generated) |
| `issued/`| Device certificates               |
| `revoked/`| Revoked certificate records      |

Set `CERTIFICATES_DIR` in `backend/.env` if using a custom path.
