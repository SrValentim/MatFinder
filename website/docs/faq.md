# FAQ

## Do I need an account to download MatFinder?

No. Downloads come straight from the public
[GitHub Releases](https://github.com/SrValentim/MatFinder/releases/latest) page —
no account, no email, no registration.

## Windows shows a SmartScreen / "unknown publisher" warning

The installer is not code-signed yet, so Windows SmartScreen may warn you the first
time you run it. This is expected for new, independent software. To proceed:

1. Click **More info**.
2. Click **Run anyway**.

The app is open-source — you can read every line on
[GitHub](https://github.com/SrValentim/MatFinder) or build it yourself
(see [Install ▸ Option 3](install.md#option-3-compile-your-own-optimized-exe)).

## Do I need Python?

Not for the pre-built Windows app — the installer and portable zip bundle everything.
You only need Python 3.11 if you want to run from source or compile your own build.

## Which databases need an API key?

Only the **Materials Project**, and its key is free. **COD**, **OQMD** and **ROD**
work with no key at all. See
[Install ▸ API key](install.md#optional-materials-project-api-key).

## Which file formats can PhaseDRX open?

PhaseDRX reads common 2θ–intensity text formats (such as `.dat`, `.xy`, `.txt`) and
aims to support instrument formats as well. CIF files are used for the theoretical
structures. If a file you expect to work does not load, please
[open an issue](https://github.com/SrValentim/MatFinder/issues) with a sample file so
we can add or fix support.

## Is it really free?

Yes — MatFinder is free and open-source under the **GPL-3.0** license. You can use,
study, modify and redistribute it under that license.

## How do I report a bug or request a feature?

Open an [issue on GitHub](https://github.com/SrValentim/MatFinder/issues) (templates
are available). See [`CONTRIBUTING.md`](https://github.com/SrValentim/MatFinder/blob/main/CONTRIBUTING.md)
for what to include.
