# Apps

One folder per app, and one folder inside it per version: `<slug>/v1/`, `<slug>/v2/`. Each app's versions are numbered from v1.
Add one with `scaffold new app <slug>`: a new slug starts at v1, a slug already here gets its next version. The manifest records each version's question and status.
A superseded version is left as it was.
