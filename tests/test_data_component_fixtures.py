"""Exact inputs, source premises and diagnostic-cause regressions for components."""
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_data_component_fixtures as generated


RUN_VARIANTS = {
    "R735": "multiple_statements",
    "R737": "plain colons",
    "R738": "public private allocatable contiguous pointer",
    "C749": "intrinsic_members prior_derived",
    "C755": "kind_len_bounds inherited_len_bound constant_property",
    "C759": "own_len_parameter deferred_allocatable deferred_pointer",
    "R741": "explicit_interface omitted_interface typed_interface multiple_declarators",
    "R742": "public private",
    "C763": "case_equivalent",
    "C765": "assumed_lengths sequence_nonpolymorphic optional_self target_self",
    "S7.5.4.1-001": "shared_parameters shared_allocatable",
    "S7.5.4.2-001": "individual dimension rank_override bound_override zero_extent",
    "S7.5.4.3-001": "individual codimension corank_override rank_and_corank",
    "S7.5.4.5-001": "component_nopass binding_nopass",
    "S7.5.4.5-002": "component_default component_pass binding_default binding_pass",
    "S7.5.4.5-003": "component_named binding_named two_binding_contexts",
}
COMPILE_VARIANTS = {
    "C749": "prior_enum prior_enumeration forward_pointer forward_allocatable",
    "C752": "unrelated_same_spelling",
}
NEGATIVE_VARIANTS = {
    "R737": "missing_colons",
    "C748": "public private allocatable codimension contiguous dimension pointer",
    "C749": "self_value forward_value",
    "C750": "pointer_local pointer_dimension allocatable_local allocatable_dimension overridden_dimension",
    "C751": ("explicit_suffix explicit_codimension missing_allocatable_suffix "
             "missing_allocatable_codimension overridden_codimension"),
    "C752": "c_ptr c_ptr_renamed c_funptr c_funptr_renamed team_type team_type_renamed",
    "C753": "pointer allocatable array",
    "C754": "individual dimension overridden_dimension",
    "C755": "lower_variable upper_variable specification_function assumed_shape_inquiry",
    "C756": "scalar array",
    "C757": "scalar_pointer ordinary_array",
    "C758": "integer_suffix derived_suffix",
    "C759": "host_variable overridden_length procedure_constant_inquiry",
    "R741": "missing_colons",
    "C760": "public private pointer nopass pass named_pass",
    "C761": "missing_pointer",
    "C762": "omitted_interface typed_interface zero_arguments",
    "C763": "missing_name",
    "C764": "bare named",
    "C765": ("procedure_dummy array_self_component array_self_binding "
             "pointer_self_component pointer_self_binding allocatable_self_component allocatable_self_binding "
             "other_type_component other_type_binding length_n_component length_n_binding "
             "length_m_component length_m_binding nonpolymorphic_component nonpolymorphic_binding "
             "value_self_component value_self_binding classof_sequence"),
}
EXTRA_CONTROLS = {
    "C749": "self_allocatable_repair",
    "C756": "scalar_pointer_repair array_pointer_repair",
    "C764": "bare_nopass_repair named_nopass_repair",
}


def identifier(rule, variant, invalid=False):
    return (rule.replace(".", "_").replace("-", "_")
            + ("_invalid__" if invalid else "_valid__") + variant)


class DataComponentFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases
                     if "/fixtures/data_component_" in case.path}
        cls.negatives = {name: case for name, case in cls.cases.items() if case.kind == "invalid"}

    def inputs(self, name):
        case = self.cases[name]
        return {file: (case.fixture.root / file).read_bytes() for file in case.fixture.files}

    def source(self, name):
        return b"\n".join(self.inputs(name).values())

    def judge(self, case, message, family="lfortran", code=1, line=None, filename=None,
              end_line=None, suffix="", timed_out=False, echo=False):
        diagnostic = case.fixture.expectation.diagnostic
        line = diagnostic["line"] if line is None else line
        filename = filename or diagnostic["file"]
        if family == "lfortran":
            header = f"{filename}:{line}-{line if end_line is None else end_line}:1-90: semantic error: "
        else:
            header = f"{filename}:{line}:1: error: "
        output = header + ("unrelated error" if echo else message) + "\n"
        if echo:
            output += "   1 | " + message + "\n"
        result = runner.ProcessResult(code, output + suffix, timed_out=timed_out)
        compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023")
        return runner.judge_diagnostic(result, compiler, case.rule, diagnostic).outcome

    def test_exact_independent_id_inventory_and_phases(self):
        expected = {}
        for phase, groups in (("run", RUN_VARIANTS), ("compile", COMPILE_VARIANTS),
                              ("compile", EXTRA_CONTROLS)):
            for rule, variants in groups.items():
                for variant in variants.split():
                    expected[identifier(rule, variant)] = phase
        for rule, variants in NEGATIVE_VARIANTS.items():
            for variant in variants.split():
                expected[identifier(rule, variant, True)] = "compile"
                control = {
                    ("C761", "missing_pointer"): "pointer_repair",
                    ("C759", "procedure_constant_inquiry"): "procedure_parameter_repair",
                    ("C765", "classof_sequence"): "typeof_sequence_repair",
                }.get((rule, variant), variant + "_repair")
                expected[identifier(rule, control)] = "compile"
        self.assertEqual(len(expected), 211)
        self.assertEqual(set(self.cases), set(expected))
        self.assertEqual(set(self.specs), set(expected))
        self.assertEqual(len(self.negatives), 77)
        self.assertEqual(sum(phase == "run" for phase in expected.values()), 47)
        self.assertEqual(sum(case.meta.coarray for case in self.cases.values()), 35)
        for name, phase in expected.items():
            case = self.cases[name]
            with self.subTest(case=name):
                self.assertEqual(case.fixture.expectation.phase, phase)
                self.assertEqual(self.specs[name]["phase"], phase)
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.images, 1)
                self.assertEqual(case.meta.profiles, [])
                self.assertEqual(case.meta.evidence, self.specs[name]["evidence"])
                self.assertEqual(case.meta.coarray, self.specs[name]["coarray"])
                self.assertIn(generated.source_name(case.rule), case.fixture.files)

    def test_exact_generated_bytes_and_confined_prefix(self):
        for path, raw in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/data_component_"))
                raw.decode("ascii")
                self.assertTrue(raw.endswith(b"\n"))
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        actual = {p for p in (ROOT / "tests/fixtures").glob("data_component_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        self.assertEqual(len(actual), 430)

    def test_every_negative_has_exact_minimal_controls(self):
        self.assertEqual(set(self.repairs), set(self.negatives))
        self.assertEqual(sum(map(len, self.repairs.values())), 82)
        for name, controls in self.repairs.items():
            bad = self.inputs(name)
            for repair in controls:
                good = self.inputs(repair["control"])
                with self.subTest(case=name, control=repair["control"]):
                    file = repair["file"]
                    self.assertEqual(set(bad), set(good))
                    self.assertEqual([key for key in bad if bad[key] != good[key]], [file])
                    wrong, fixed = repair["wrong"].encode(), repair["repaired"].encode()
                    self.assertEqual(bad[file].count(wrong), 1)
                    self.assertEqual(bad[file].replace(wrong, fixed, 1), good[file])
                    self.assertEqual(self.cases[name].meta.coarray,
                                     self.cases[repair["control"]].meta.coarray)
                    self.assertEqual(self.cases[repair["control"]].fixture.expectation.phase, "compile")
        self.assertEqual(len(self.repairs["C749_invalid__self_value"]), 2)
        for name in ("C756_invalid__scalar", "C756_invalid__array",
                     "C764_invalid__bare", "C764_invalid__named"):
            self.assertEqual(len(self.repairs[name]), 2)

    def test_prospective_cause_predicates_are_not_observation_claims(self):
        for name, case in self.negatives.items():
            for message in case.fixture.expectation.diagnostic["contains_any"]:
                self.assertNotIn(message.lower(), {"type", "kind", "constant", "attribute", "expected", "function"})
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, message=message, family=family, code=code):
                            self.assertEqual(self.judge(case, message, family, code), "pass")

    def test_unsupported_capability_wrappers_never_receive_diagnostic_credit(self):
        prefixes = ("Unsupported: ", "This feature is unsupported by this compiler: ")
        positives = rejections = 0
        for name, case in self.negatives.items():
            message = case.fixture.expectation.diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    with self.subTest(case=name, family=family, code=code, prefix=None):
                        self.assertEqual(self.judge(case, message, family, code), "pass")
                        positives += 1
                    for prefix in prefixes:
                        with self.subTest(case=name, family=family, code=code, prefix=prefix):
                            self.assertEqual(self.judge(case, prefix + message, family, code), "fail")
                            rejections += 1
        self.assertEqual(positives, 462)
        self.assertEqual(rejections, 924)

    def test_other_type_binding_has_a_nonpassed_defining_type_witness(self):
        bad = self.inputs("C765_invalid__other_type_binding")["C765.f90"]
        good = self.inputs("C765_valid__other_type_binding_repair")["C765.f90"]
        wrong_self = b"class(other), intent(in) :: self"
        repaired_self = b"class(record), intent(in) :: self"
        witness = b"class(record), intent(in) :: witness"
        self.assertEqual(bad.replace(wrong_self, repaired_self, 1), good)
        for raw, self_declaration in ((bad, wrong_self), (good, repaired_self)):
            self.assertIn(b"subroutine action(self, witness)\n", raw)
            self.assertIn(b"procedure :: action\n", raw)
            self.assertEqual(raw.count(witness), 1)
            self.assertLess(raw.index(self_declaration), raw.index(witness))
            self.assertNotIn(b"nopass", raw)
            self.assertNotIn(b"pass(", raw)
        relation = self.repairs["C765_invalid__other_type_binding"][0]["relation"]
        self.assertIn("C784", relation)
        for name in ("C765_invalid__other_type_component", "C765_valid__other_type_component_repair"):
            raw = self.source(name)
            self.assertIn(b"subroutine iface(self)\n", raw)
            self.assertNotIn(b"witness", raw)
        for name, case in self.cases.items():
            if case.rule == "C765" and name not in (
                    "C765_invalid__other_type_binding", "C765_valid__other_type_binding_repair"):
                self.assertNotIn(b"witness", self.source(name))

    def test_generic_and_wrong_subject_messages_fail(self):
        messages = [
            "expected type", "expected attribute", "expected constant expression",
            "Unknown type 'record'", "Duplicate attribute", "Unexpected end of file",
            "Expected END TYPE statement", "Module 'definitions' was not found",
            "Component 'other' has duplicate POINTER attributes",
            "Procedure component 'other' must have the POINTER attribute",
            "Passed-object dummy argument of 'other' at (1) must be scalar",
            "Only Integer literals or expressions which reduce to constant Integer are accepted as kind parameters",
        ]
        for name, case in self.negatives.items():
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    for message in messages:
                        with self.subTest(case=name, family=family, code=code, message=message):
                            self.assertEqual(self.judge(case, message, family, code), "fail")

    def test_opposite_predicates_and_roles_at_every_allowed_location(self):
        examples = {
            "C750_invalid__pointer_local": "Component 'field' with ALLOCATABLE must have deferred shape",
            "C750_invalid__overridden_dimension": "POINTER component 'field' cannot have explicit shape",
            "C751_invalid__explicit_suffix": "Coarray component 'field' must have the ALLOCATABLE attribute",
            "C751_invalid__missing_allocatable_suffix": "Coarray component 'field' must have deferred coshape",
            "C751_invalid__overridden_codimension": "Explicit coshape is not permitted for coarray component 'field'",
            "C753_invalid__allocatable": "Coarray component 'co' must have the ALLOCATABLE attribute",
            "C753_invalid__pointer": "Component 'field' with coarray potential subobjects must be scalar",
            "C754_invalid__overridden_dimension": "Deferred shape is not permitted for ordinary component 'field'",
            "C757_invalid__scalar_pointer": "CONTIGUOUS component 'field' must have the POINTER attribute",
            "C757_invalid__ordinary_array": "CONTIGUOUS pointer component 'field' must be an array",
            "C759_invalid__procedure_constant_inquiry": "Procedure component 'action' result length is not constant",
            "C759_invalid__overridden_length": "Individual length suffix of component 'field' is not constant",
            "C761_invalid__missing_pointer": "Procedure 'action' must have the EXTERNAL attribute",
            "C762_invalid__omitted_interface": "Procedure component 'action' with no dummy arguments requires NOPASS",
            "C762_invalid__zero_arguments": "Procedure component 'action' with an implicit interface requires NOPASS",
            "C763_invalid__missing_name": "Passed-object dummy argument 'tag' of 'action' must have type 'record'",
            "C764_invalid__named": "Procedure component 'action' has duplicate PASS(self) attributes",
            "C765_invalid__pointer_self_component": "Procedure component 'action' must have the POINTER attribute",
            "C765_invalid__array_self_binding": "Passed-object dummy argument of 'action' at (1) must not be POINTER",
            "C765_invalid__value_self_component": "VALUE dummy 'self' must not have INTENT(OUT)",
            "C765_invalid__classof_sequence": "CLASS type specifier must specify an extensible type",
        }
        for kind in ("component", "binding"):
            for bad, good in (("n", "m"), ("m", "n")):
                examples[f"C765_invalid__length_{bad}_{kind}"] = (
                    f"Length parameter '{good}' of passed-object dummy 'self' in 'action' must be assumed")
        for name, message in examples.items():
            case = self.negatives[name]
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, line=line, family=family, code=code):
                            self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_unsupported_wrong_file_echo_and_abnormal_execution_are_not_diagnostics(self):
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            message = diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    for kwargs in (
                        {"filename": "other.f90"}, {"line": diagnostic["line"] - 1},
                        {"line": diagnostic.get("end_line", diagnostic["line"]) + 1},
                        {"echo": True}, {"suffix": "ASR verify pass error\n"},
                        {"suffix": "LLVM ERROR: invalid IR\n"},
                        {"suffix": "error: out of memory\n"}, {"timed_out": True},
                    ):
                        with self.subTest(case=name, family=family, code=code, kwargs=kwargs):
                            self.assertEqual(self.judge(case, message, family, code, **kwargs), "fail")
                for code in (-11, 139):
                    self.assertEqual(self.judge(case, message, family, code), "fail")
                for prefix in ("Not yet implemented: ", "Unsupported feature: ", "Obsolescent feature: "):
                    self.assertEqual(self.judge(case, prefix + message, family), "fail")
            self.assertEqual(self.judge(case, message,
                                       end_line=diagnostic.get("end_line", diagnostic["line"]) + 1), "fail")

    def test_diagnostic_text_cannot_retarget_a_second_location(self):
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            file, line = diagnostic["file"], diagnostic["line"]
            message = diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                embedded = (f"{file}:{line}-{line}:1-90: semantic error: {message}" if family == "lfortran"
                            else f"{file}:{line}:1: error: {message}")
                outer = ("other.f90:1-1:1-90: semantic error: " if family == "lfortran"
                         else "other.f90:1:1: error: ")
                for code in (0, 1):
                    compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023")
                    with self.subTest(case=name, family=family, code=code):
                        result = runner.judge_diagnostic(
                            runner.ProcessResult(code, outer + embedded + "\n"), compiler, case.rule, diagnostic)
                        self.assertEqual(result.outcome, "fail")

    def test_nonfatal_permissions_are_exact_observed_portability_routes(self):
        permissions = {}
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            for permission in diagnostic.get("allow_nonfatal", []):
                permissions[name] = permission
                self.assertEqual(set(permission), {"compiler", "severity", "equals_any"})
                self.assertEqual(permission["compiler"], "flang")
                self.assertEqual(permission["severity"], "portability")
                for message in permission["equals_any"]:
                    for family in ("flang", "gfortran"):
                        for code in (0, 1):
                            output = f"{diagnostic['file']}:{diagnostic['line']}:1: portability: {message}\n"
                            result = runner.judge_diagnostic(
                                runner.ProcessResult(code, output), runner.Compiler(family, family, "f2018"),
                                case.rule, diagnostic)
                            self.assertEqual(result.outcome, "pass" if family == "flang" else "fail")
                    for prefix in ("Not yet implemented: ", "Obsolescent feature: "):
                        output = f"{diagnostic['file']}:{diagnostic['line']}:1: portability: {prefix}{message}\n"
                        result = runner.judge_diagnostic(
                            runner.ProcessResult(0, output), runner.Compiler("flang", "flang", "f2018"),
                            case.rule, diagnostic)
                        self.assertEqual(result.outcome, "fail")
        self.assertEqual(set(permissions), {
            "C757_invalid__scalar_pointer", "C757_invalid__ordinary_array",
            "C765_invalid__pointer_self_binding",
        })

    def test_observed_routes_do_not_credit_different_properties_or_subjects(self):
        probes = {
            "C752_invalid__team_type": [
                "Component 'field' at (1) of TYPE(C_PTR) or TYPE(C_FUNPTR) shall not be a coarray"],
            "C753_invalid__pointer": [
                "Allocatable or array component 'field' may not have a coarray ultimate component '%co'"],
            "C755_invalid__assumed_shape_inquiry": ["Expression at (1) in this context must be constant"],
            "C755_invalid__specification_function": [
                "Expression at (1) in this context must be constant",
                "Invalid specification expression: reference to function 'other' not allowed for derived type components or type parameter values"],
            "C759_invalid__procedure_constant_inquiry": [
                "Character length of component 'field' needs to be a constant specification expression at (1)",
                "Procedure component 'action' requires an explicit interface"],
            "C762_invalid__zero_arguments": [
                "Procedure component 'action' must have NOPASS attribute or explicit interface"],
            "C762_invalid__typed_interface": [
                "Procedure pointer component 'action' with PASS at (1) must have at least one argument"],
            "C763_invalid__missing_name": ["'self' is not a dummy argument of procedure interface 'iface'"],
            "C765_invalid__procedure_dummy": [
                "Argument 'self' of 'action' with PASS(self) at (1) must be of the derived type 'record'"],
            "C765_invalid__classof_sequence": [
                "Argument 'self' of 'action' with PASS(self) at (1) must be of the derived type 'record'"],
        }
        for kind in ("component", "binding"):
            for parameter, other in (("n", "m"), ("m", "n")):
                probes[f"C765_invalid__length_{parameter}_{kind}"] = [
                    f"Passed-object dummy argument 'self' of procedure 'action' has non-assumed length parameter '{other}'",
                    "Argument 'self' of 'action' with PASS(self) at (1) must be of the derived type 'record'",
                    "All LEN type parameters of the passed dummy argument 'self' of 'action' at (1) must be ASSUMED.",
                ]
        for name in ("C751_invalid__explicit_suffix", "C751_invalid__explicit_codimension",
                     "C751_invalid__missing_allocatable_suffix", "C751_invalid__missing_allocatable_codimension"):
            probes[name] = ["Coarray component 'field' at (1) must be allocatable with deferred shape"]
        for name, messages in probes.items():
            case = self.negatives[name]
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        for message in messages:
                            with self.subTest(case=name, family=family, code=code, line=line, message=message):
                                self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_null_initializers_have_no_arguments(self):
        count = 0
        for name in self.cases:
            raw = self.source(name).decode().lower()
            for match in re.finditer(r"=>\s*null\s*\(([^)]*)\)", raw):
                with self.subTest(case=name):
                    self.assertEqual(match.group(1).strip(), "")
                    count += 1
            self.assertNotIn("null(mold", raw)
        self.assertGreater(count, 0)

    def test_corank_runs_have_real_guarded_allocation_premises(self):
        names = [name for name, case in self.cases.items() if case.rule == "S7.5.4.3-001"]
        self.assertEqual(len(names), 4)
        for name in names:
            case = self.cases[name]
            raw = self.source(name).decode().lower()
            with self.subTest(case=name):
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertTrue(case.meta.coarray)
                self.assertIn("type(record), save :: value", raw)
                self.assertNotIn("pointer", raw)
                guard = raw.index("if (num_images() /= 1) error stop 1")
                allocations = list(re.finditer(r"(?m)^allocate\(value%(\w+).*stat=stat\)", raw))
                deallocations = list(re.finditer(r"(?m)^deallocate\(value%(\w+), stat=stat\)", raw))
                self.assertEqual([m.group(1) for m in allocations], [m.group(1) for m in deallocations])
                self.assertTrue(allocations)
                self.assertTrue(all(guard < m.start() for m in allocations))
                first_inquiry = raw.index("lcobound(")
                self.assertTrue(all(m.start() < first_inquiry for m in allocations))
                for match in allocations:
                    field = match.group(1)
                    self.assertIn(f"if (.not. allocated(value%{field})) error stop 4", raw)
                self.assertNotIn("stop 77", raw)
                self.assertNotRegex(raw, r"(?<!_)corank\s*\(")

    def test_constant_procedure_result_candidate_has_exact_reviewed_layout(self):
        bad = self.inputs("C759_invalid__procedure_constant_inquiry")["C759.f90"].decode().lower()
        good = self.inputs("C759_valid__procedure_parameter_repair")["C759.f90"].decode().lower()
        expression = "merge(2,3,same_type_as(a,b))"
        self.assertEqual(bad.replace(expression, "2"), good)
        self.assertLess(bad.index("type(carrier) :: a, b"), bad.index("type :: record"))
        self.assertIn("integer, public :: payload", bad)
        self.assertIn("pointer, nopass :: action", bad)
        for forbidden in ("sequence", "bind(c)", "class(", "a%payload", "b%payload", "call ", "len=width"):
            self.assertNotIn(forbidden, bad)
        diagnostic = self.negatives["C759_invalid__procedure_constant_inquiry"].fixture.expectation.diagnostic
        self.assertIn("must be constant", diagnostic["excludes_any"])

    def test_nonextensible_passed_object_candidate_keeps_seed_import_order(self):
        bad = self.inputs("C765_invalid__classof_sequence")["C765.f90"].decode().lower()
        good = self.inputs("C765_valid__typeof_sequence_repair")["C765.f90"].decode().lower()
        self.assertEqual(bad.replace("classof(seed)", "typeof(seed)"), good)
        ordered = ["type :: record", "sequence", "end type", "type(record) :: seed",
                   "abstract interface", "import :: seed", "classof(seed), intent(in) :: self"]
        positions = [bad.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("integer, public :: payload", bad)
        self.assertIn("procedure(iface), pointer, public :: action", bad)
        for forbidden in ("private", "bind(c)", "class(record)", "same_type_as", "seed%", "contains"):
            self.assertNotIn(forbidden, bad)

    def test_len_negative_roles_are_independent_and_value_has_no_intent_conflict(self):
        for kind in ("component", "binding"):
            for parameter, selector in (("n", "2,*"), ("m", "*,3")):
                name = f"C765_invalid__length_{parameter}_{kind}"
                raw = self.source(name).decode().lower()
                self.assertIn(f"class(record({selector})), intent(in) :: self", raw)
                self.assertIn("integer, len :: n,m", raw)
                self.assertNotIn("integer, kind", raw)
            value = self.source("C765_invalid__value_self_" + kind).lower()
            self.assertIn(b"class(record), value, intent(in) :: self", value)
            self.assertNotIn(b"intent(out)", value)
            self.assertNotIn(b"intent(inout)", value)

    def test_array_override_and_zero_extent_oracles_are_not_storage_guesses(self):
        rank = self.source("S7_5_4_2_001_valid__rank_override").lower()
        self.assertIn(b"dimension(2,3) :: local(4), inherited", rank)
        self.assertIn(b"rank(value%local) /= 1", rank)
        bounds = self.source("S7_5_4_2_001_valid__bound_override").lower()
        self.assertIn(b"dimension(-1:1) :: local(2:4), inherited", bounds)
        self.assertIn(b"lbound(value%local,1) /= 2", bounds)
        empty = self.source("S7_5_4_2_001_valid__zero_extent").lower()
        self.assertNotIn(b"value%field(", empty)
        self.assertNotIn(b"lbound", empty)
        self.assertNotIn(b"ubound", empty)
        for name in self.cases:
            self.assertNotRegex(self.source(name).lower(),
                                rb"\b(?:transfer|storage_size|c_sizeof|sizeof|offsetof|c_loc)\s*\(")

    def test_overridden_specifications_and_leaf_coarray_remain_unchanged(self):
        for name, bad_shape, good_shape in (
            ("C750_invalid__overridden_dimension", b"dimension(2) :: field(:)", b"dimension(:) :: field(:)"),
            ("C751_invalid__overridden_codimension", b"codimension[*] :: field[:]", b"codimension[:] :: field[:]"),
            ("C754_invalid__overridden_dimension", b"dimension(:) :: field(2)", b"dimension(3) :: field(2)"),
            ("C759_invalid__overridden_length", b"len=width) :: field*2", b"len=2) :: field*2"),
        ):
            self.assertIn(bad_shape, self.source(name))
            self.assertIn(good_shape, self.source(self.repairs[name][0]["control"]))
        for variant in ("pointer", "allocatable", "array"):
            name = "C753_invalid__" + variant
            for current in (name, self.repairs[name][0]["control"]):
                self.assertIn(b"integer, allocatable :: co[:]", self.source(current))

    def test_canonical_and_graph_facets_do_not_acquire_wrapper_execution_credit(self):
        prohibited = {
            "empty-part-link", "data-alternative-link", "procedure-alternative-link",
            "type-specifier-use-graph", "named-list", "individual-array-link", "individual-coarray-link",
            "individual-character-link", "initialization-use-graph", "explicit-shape-link",
            "deferred-shape-link", "general-array-grammar-exclusion-graph", "not-coarray-interaction",
            "nested-and-inherited-use-graph", "forbidden-reference-use-graph", "transfer-qualification-graph",
            "array-pointer-admission-link", "character-suffix-admission-link", "assumed-star-canonical-link",
            "expression-context-use-graph", "nopass-link", "bare-pass-link", "named-pass-link", "pointer-link",
            "explicit-passed-object-boundary", "character-override-link", "dimension-override-link",
            "codimension-override-link", "inherited-context-link", "parameter-scope-boundary",
        }
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertFalse(set(case.meta.facets) & prohibited)
                self.assertNotIn(case.rule, {"R736", "R739", "R740", "C766", "C767", "C768", "C769", "C770", "C771"})
        self.assertIn("indirection-boundaries", self.cases["C749_valid__self_value_repair"].meta.facets)
        self.assertNotIn("C749_valid__self_pointer", self.cases)

    def test_pending_partition_uses_actual_case_facets_not_administrative_review_state(self):
        covered = {}
        for case in self.all_cases:
            covered.setdefault(case.rule, set()).update(case.meta.facets)
        linked = self.registry.evidence.validate_cases(self.all_cases)
        for section in (f"7.5.4.{i}" for i in range(1, 6)):
            for requirement in self.registry.catalogues[section]["requirements"]:
                rule = requirement["id"]
                self.assertEqual(set(requirement["pending"]),
                                 set(requirement["facets"]) - covered.get(rule, set()) - set(linked.get(rule, {})))


if __name__ == "__main__":
    unittest.main()
