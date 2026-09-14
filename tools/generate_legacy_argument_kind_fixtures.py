#!/usr/bin/env python3
"""Generate the isolated, processor-qualified legacy argument-kind cases."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE = "S15.5.2.4"


def cases():
    real = ["real-kinds-4-8"]
    literal = ["real-kinds-4-8", "default-real-kind-4"]
    return [
        ("real4-to-real8", real, """subroutine s15524_real4_to_real8()
    implicit none
    real(4) :: a = 1.0
    call s(a)
contains
    subroutine s(x)
        real(8), intent(in) :: x
    end subroutine
end subroutine
""", "real(8), intent(in) :: x", "real(4), intent(in) :: x", "call s(a)"),
        ("real8-to-real4", real, """subroutine s15524_real8_to_real4()
    implicit none
    real(8) :: a = 1.0d0
    call s(a)
contains
    subroutine s(x)
        real(4), intent(in) :: x
    end subroutine
end subroutine
""", "real(4), intent(in) :: x", "real(8), intent(in) :: x", "call s(a)"),
        ("int4-to-int8", ["integer-kinds-4-8"], """subroutine s15524_int4_to_int8()
    implicit none
    integer(4) :: n = 1
    call s(n)
contains
    subroutine s(x)
        integer(8), intent(in) :: x
    end subroutine
end subroutine
""", "integer(8), intent(in) :: x", "integer(4), intent(in) :: x", "call s(n)"),
        ("literal-real4-to-real8", literal, """subroutine s15524_literal_real4_to_real8()
    implicit none
    call s(1.0)
contains
    subroutine s(x)
        real(8), intent(in) :: x
    end subroutine
end subroutine
""", "call s(1.0)", "call s(1.0_8)", "call s(1.0)"),
        ("logical1-to-logical4", ["logical-kinds-1-4"], """subroutine s15524_logical1_to_logical4()
    implicit none
    logical(1) :: l = .true._1
    call s(l)
contains
    subroutine s(x)
        logical(4), intent(in) :: x
    end subroutine
end subroutine
""", "logical(4), intent(in) :: x", "logical(1), intent(in) :: x", "call s(l)"),
        ("char4-to-char1", ["character-kinds-1-4-iso10646"], """subroutine s15524_char4_to_char1()
    implicit none
    character(kind=4, len=1) :: c = 4_"a"
    call s(c)
contains
    subroutine s(x)
        character(kind=1, len=1), intent(in) :: x
    end subroutine
end subroutine
""", "character(kind=1, len=1), intent(in) :: x",
         "character(kind=4, len=1), intent(in) :: x", "call s(c)"),
        ("function-arg-real4-to-real8", literal, """subroutine s15524_function_result_kind()
    implicit none
    real(8) :: y
    y = f(1.0)
contains
    real(8) function f(x)
        real(8), intent(in) :: x
        f = x
    end function
end subroutine
""", "f(1.0)", "f(1.0_8)", "y = f(1.0)"),
        ("module-procedure-real4-to-real8", literal, """module s15524_m
    implicit none
contains
    subroutine t(x)
        real(8), intent(in) :: x
    end subroutine
end module
subroutine s15524_module_procedure()
    use s15524_m
    implicit none
    call t(1.0)
end subroutine
""", "call t(1.0)", "call t(1.0_8)", "call t(1.0)"),
    ]


def outputs():
    result = {}
    for name, profiles, negative, wrong, repaired, statement in cases():
        if negative.count(wrong) != 1:
            raise ValueError(f"{name}: repair is not a unique substitution")
        locations = [line for line, text in enumerate(negative.splitlines(), 1)
                     if text.strip() == statement]
        if len(locations) != 1:
            raise ValueError(f"{name}: diagnostic statement is not unique")
        for invalid in (True, False):
            kind = "invalid" if invalid else "valid"
            folder = ROOT / "tests" / "fixtures" / f"legacy_argument_{name.replace('-', '_')}_{kind}"
            source = negative if invalid else negative.replace(wrong, repaired, 1)
            identifier = (f"S15_5_2_4_invalid:{name}" if invalid
                          else f"S15_5_2_4_valid__{name}_repair")
            manifest = {
                "schema_version": 1,
                "id": identifier,
                "rule": RULE,
                "facets": [],
                "evidence": "effect" if invalid else "positive-control",
                "profiles": profiles,
                "oracle_basis": "lfortran-policy" if invalid else "standard",
                "files": ["source.f90"],
                "build": [{"id": "source", "source": "source.f90", "language": "fortran",
                           "form": "free", "output": "source.o"}],
                "expect": {"phase": "compile", "step": "source",
                           "outcome": "reject" if invalid else "success"},
            }
            if invalid:
                manifest["expect"]["diagnostic"] = {"file": "source.f90", "line": locations[0]}
            result[folder / "source.f90"] = source.encode("ascii")
            result[folder / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated files without writing")
    args = parser.parse_args()
    expected = outputs()
    if args.check:
        mismatches = [str(path.relative_to(ROOT)) for path, data in expected.items()
                      if not path.is_file() or path.read_bytes() != data]
        if mismatches:
            parser.error("generated inputs differ: " + ", ".join(mismatches))
    else:
        for path, data in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'Checked' if args.check else 'Generated'} 16 legacy argument fixtures, {len(expected)} files.")


if __name__ == "__main__":
    main()
