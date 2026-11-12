# Contributing

## Branch and pull-request workflow

1. Start from an up-to-date `main`: `git switch main` then `git pull --ff-only`.
2. Create a focused branch: `git switch -c feat/short-description` (or `fix/` / `docs/`).
3. Make a small change, run the checks below and inspect `git diff --check` and `git diff`.
4. Commit with a descriptive message, push the branch and open a pull request against `main`.
5. Explain the reason, validation results and hardware limitations. Resolve failing checks before merging.

Do not commit credentials, personal recordings, local environments or generated builds. Preserve third-party notices and research provenance. Report a reproducible issue with environment/tool versions before proposing a fix.

## Local checks

Run from the repository root with Python 3.12. Install the listed tools in a virtual environment; system tools must be on PATH.

```sh
python tools/check_repository.py
python -m pip install ruff==0.11.13
ruff check .
python -m pip install clang-format==18.1.8
python tools/format_sources.py --check
cppcheck --enable=warning,performance,portability --error-exitcode=1 --inline-suppr --suppress=missingIncludeSystem --suppress=missingInclude --suppress=unmatchedSuppression --language=c --std=c11 -DUSE_HAL_DRIVER -DSTM32F103xB -Ifirmware/Core/Inc firmware/Core/Src/main.c firmware/Core/Src/lcd_i2c.c
cmake -S firmware -B build/firmware -G Ninja -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build/firmware
python -m pip install pytest==8.3.5
python -m pytest host/tests/test_parser.py -q
```

## What CI establishes

CI checks local Markdown links, source syntax and unresolved merge markers. External links are not polled on every push. Ruff checks syntax and selected correctness rules without requiring hardware libraries. clang-format 18 covers application files; vendored STM32 drivers are excluded. cppcheck analyzes application sources without claiming to replace the target compiler; SDK include-resolution messages are suppressed. CMake cross-compiles the STM32F103C8 firmware and emits ELF/HEX/BIN files. Install ARM GNU, newlib, CMake and Ninja locally. Set PYTHONPATH=host/src for the existing parser tests. Sensor accuracy and flashing require hardware.

These workflows run on pushes and pull requests with read-only repository permissions and bounded execution time. A green check applies to the checks listed here; it does not establish physical hardware validation.
