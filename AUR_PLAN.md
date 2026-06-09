# AUR Package Plan — minq-nhentai

Apply these changes when ready to distribute as an Arch AUR package.

## Files to modify

### 1. `pyproject.toml` — Add entry point + project URLs

Insert after the `[project.optional-dependencies]` block:

```toml
[project.scripts]
minq-nhentai = "minq_nhentai.cli:main"

[project.urls]
Homepage = "https://github.com/kuche1/minq-nhentai"
Repository = "https://github.com/kuche1/minq-nhentai"
```

This creates a `minq-nhentai` CLI command at install time.

### 2. `PKGBUILD` — Create at repo root

```bash
# Maintainer: REDCODE <aironerowork@gmail.com>

pkgname=minq-nhentai
pkgver=0.2.0
pkgrel=1
pkgdesc="Terminal-based nhentai reader with sixel image support"
arch=('any')
url="https://github.com/kuche1/minq-nhentai"
license=('GPL2')
depends=(
  'python'
  'python-beautifulsoup4'
  'python-requests'
  'python-lxml'
  'python-pillow'
)
makedepends=(
  'python-build'
  'python-installer'
  'python-wheel'
  'python-setuptools'
)
optdepends=(
  'libsixel: provides img2sixel for sixel image backend'
  'viu: alternative image backend using viu'
)
source=("$pkgname-$pkgver.tar.gz::https://github.com/kuche1/minq-nhentai/archive/8082a7c.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$srcdir/$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$srcdir/$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl
}

# vim:set ts=2 sw=2 et:
```

**Note**: The extracted directory name from a commit-archive tarball follows the pattern `minq-nhentai-<short_hash>`. The `build()` and `package()` functions use `$srcdir/$pkgname-$pkgver` which assumes a versioned tag. If the directory name doesn't match, use `$srcdir/*/` or update `pkgver` to `0.2.0.r0.g8082a7c` (or use `git describe` style versioning). **Test with `makepkg` before submitting to AUR.**

### 3. `.SRCINFO` — Generate after PKGBUILD is finalized

```bash
makepkg --printsrcinfo > .SRCINFO
```

This must be regenerated whenever PKGBUILD changes.

## Pre-submit checklist

- [ ] Owner transfers the repo (so master becomes the active branch)
- [ ] A git tag (e.g. `v0.2.0`) is created pointing to the release commit
- [ ] Update `PKGBUILD` to use the tag-based tarball URL and real sha256sum
- [ ] Regenerate `.SRCINFO` from the final PKGBUILD
- [ ] Submit to AUR via `git push` to `ssh://aur@aur.archlinux.org/minq-nhentai.git`

## Notes

- External binaries (`img2sixel`, `viu`) are optional — declared as `optdepends`
- The package auto-detects which backend is available at runtime
- Python deps map directly to Arch community packages: `python-beautifulsoup4`, `python-requests`, `python-lxml`, `python-pillow`
