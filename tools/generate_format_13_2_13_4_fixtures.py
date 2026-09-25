#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 FORMAT specifications and format control."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, wrong_oracle_source

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "format_13_2_13_4"
SUMMARY_BEGIN = "<!-- BEGIN FORMAT 13.2-13.4 FIXTURES -->"
SUMMARY_END = "<!-- END FORMAT 13.2-13.4 FIXTURES -->"
CATALOGUES = {
    "13.2.1": "doc/catalogues/format_statement_13_2_1.json",
    "13.2.2": "doc/catalogues/character_format_specification_13_2_2.json",
    "13.3.1": "doc/catalogues/format_item_list_syntax_13_3_1.json",
    "13.4": "doc/catalogues/interaction_between_input_output_list_and_format_13_4.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}


def case(variant, section, rule, facet, category, title, declarations, setup, actions,
         checks, features, derivation):
    evidence = "effect" if category == "effect" else "positive-control"
    return dict(variant=variant, section=section, rule=rule, facets=[facet], category=category,
                evidence=evidence, title=title, declarations=declarations, setup=setup,
                actions=actions, checks=checks, features=features, derivation=derivation)


def char_check(expr, expected, label="observed"):
    return dict(kind="char", expr=expr, expected=expected, label=label)


CASES = [
    case("format_stmt_keyword_spec", "13.2.1", "R1301", "format-keyword-with-specification", "syntax",
         "FORMAT statement supplies format specification",
         ["character(len=3) :: buf"], ["buf = '###'"],
         ["100 format(SS,I3)", "write(buf,100) 7"], [char_check("buf", "  7")],
         [("format-stmt-specification", "100 format(SS,I3)", "100 format(SS,I2)")],
         "R1301 parses FORMAT followed by (I3); I3 writes integer 7 right-justified in width 3."),
    case("format_items_parenthesized", "13.2.1", "R1302", "format-items-parenthesized", "syntax",
         "Parenthesized format items",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,I3)') 7"],
         [char_check("buf", "  7")], [("parenthesized-format-item", "'(SS,I3)'", "'(SS,I2)'")],
         "R1302 parenthesizes the I3 item; I3 writes 7 in a three-character field."),
    case("empty_parenthesized_format", "13.2.1", "R1302", "empty-parenthesized-format", "syntax",
         "Empty parenthesized format with no item",
         ["character(len=1) :: buf"], ["buf = '#'"], ["write(buf,'()')"],
         [char_check("buf", " ")], [("empty-format-to-character", "'()'", "'(\"X\")'")],
         "R1302 permits an empty parenthesized specification; with no list item the internal record is blank."),
    case("unlimited_format_item_form", "13.2.1", "R1302", "unlimited-format-item-form", "syntax",
         "Unlimited format item in format specification",
         ["character(len=5) :: buf"], ["buf = '#####'"], ["write(buf,'(SS,*(I1,:,\",\"))') 1,2,3"],
         [char_check("buf", "1,2,3")], [("unlimited-asterisk", "'(SS,*(I1,:,\",\"))'", "'(SS,2(I1,:,\",\"))'")],
         "R1302 admits an unlimited-format-item after format-items; p8 reuses it without record advancement for 1,2,3."),
    case("labelled_format_stmt", "13.2.1", "C1301", "labelled-format-stmt", "restriction",
         "Labelled FORMAT statement selected by label",
         ["character(len=2) :: buf"], ["buf = '##'"],
         ["100 format(SS,I2)", "200 format(SS,I1)", "write(buf,100) 8"], [char_check("buf", " 8")],
         [("referenced-format-label", "write(buf,100) 8", "write(buf,200) 8")],
         "C1301 is satisfied by labelled FORMAT 100; WRITE using label 100 applies I2 to produce blank then 8."),
    case("embedded_blanks_between_descriptors", "13.2.1", "S13.2.1-001", "embedded-blanks-between-descriptors", "effect",
         "Insignificant blanks between format descriptors",
         ["character(len=5) :: buf"], ["buf = '#####'"], ["write(buf,'( SS , I3 , 1X , I1 )') 7,4"],
         [char_check("buf", "  7 4")], [("blanked-format-control", "1X", "2X")],
         "13.2.1 p1 gives blanks outside strings no effect; the significant I3, 1X, and I1 descriptors produce '  7 4'."),
    case("leading_blanks_before_format", "13.2.1", "S13.2.1-001", "leading-blanks-before-format", "effect",
         "Blank characters before the initial left parenthesis are ignored",
         ["character(len=10) :: fmt", "character(len=3) :: buf"], ["fmt = '   (SS,I3)'", "buf = '###'"],
         ["write(buf,fmt) 7"], [char_check("buf", "  7")],
         [("leading-blank-format-descriptor", "fmt = '   (SS,I3)'", "fmt = '   (SS,I2)'")],
         "13.2.1 p1 permits blanks before the initial left parenthesis; after ignoring them, (I3) writes 7 in width 3."),
    case("character_string_blanks_preserved", "13.2.1", "S13.2.1-001", "character-string-blanks-preserved", "effect",
         "Blank inside character string descriptor is significant",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(\"A B\")')"],
         [char_check("buf", "A B")], [("string-blank", "\"A B\"", "\"AXB\"")],
         "13.2.1 p1 excludes character string edit descriptors from blank elision, so the embedded blank is output."),
    case("leading_valid_character_format", "13.2.2", "S13.2.2-001", "leading-valid-format", "restriction",
         "Leading valid format ignores following characters",
         ["character(len=10) :: fmt", "character(len=3) :: buf"], ["fmt = '(SS,I3)XYZ'", "buf = '###'"],
         ["write(buf,fmt) 7"], [char_check("buf", "  7")], [("leading-format-descriptor", "'(SS,I3)XYZ'", "'(SS,I2)XYZ'")],
         "13.2.2 p1 requires the leading part to be a valid format; the leading (I3) writes 7 in width 3."),
    case("defined_through_final_parenthesis", "13.2.2", "S13.2.2-002", "defined-through-final-parenthesis", "restriction",
         "Defined positions through final right parenthesis",
         ["character(len=7) :: fmt", "character(len=3) :: buf"], ["fmt = '#######'", "fmt(1:7) = '(SS,I3)'", "buf = '###'"],
         ["write(buf,fmt) 7"], [char_check("buf", "  7")], [("defined-format-positions", "fmt(1:7) = '(SS,I3)'", "fmt(1:7) = '(SS,I2)'")],
         "All characters through the final right parenthesis are defined as (I3) before the WRITE executes."),
    case("trailing_characters_ignored", "13.2.2", "S13.2.2-002", "trailing-characters-ignored", "restriction",
         "Characters after final right parenthesis do not affect interpretation",
         ["character(len=9) :: fmt_a, fmt_b", "character(len=3) :: a, b", "character(len=6) :: observed"],
         ["fmt_a = '(SS,I3)AB'", "fmt_b = '(SS,I3)WX'", "a = '###'", "b = '###'", "observed = '######'"],
         ["write(a,fmt_a) 7", "write(b,fmt_b) 7", "observed = a // b"], [char_check("observed", "  7  7")],
         [("second-leading-descriptor", "fmt_b = '(SS,I3)WX'", "fmt_b = '(SS,I2)WX'")],
         "13.2.2 p2 says characters after the final right parenthesis have no effect; two different suffixes give the same I3 field."),
    case("rank_one_character_array_concat", "13.2.2", "S13.2.2-003", "rank-one-character-array-concatenation", "effect",
         "Rank-one character array supplies concatenated format",
         ["character(len=4) :: fmt(2)", "character(len=3) :: buf"], ["fmt = [character(len=4) :: '(SS', ',I3)']", "buf = '###'"],
         ["write(buf,fmt) 7"], [char_check("buf", "  7")], [("array-format-element", "',I3)'", "',I2)'")],
         "13.2.2 p3 treats the array elements as concatenated, yielding the format specification (I3)."),
    case("array_element_order_concat", "13.2.2", "S13.2.2-003", "array-element-order-concatenation", "effect",
         "Character array elements concatenate in array element order",
         ["character(len=4) :: fmt(4)", "character(len=3) :: buf"],
         ["fmt = [character(len=4) :: '(SS', ',I1', ',I1', ')   ']", "buf = '###'"], ["write(buf,fmt) 2,5"],
         [char_check("buf", "25 ")], [("middle-array-element", "fmt = [character(len=4) :: '(SS', ',I1', ',I1', ')   ']", "fmt = [character(len=4) :: '(SS', ',I1', ',I2', ')   ']")],
         "Array element order concatenates '(I1', ',I1', ')  ' to a leading '(SS,I1,I1)' format, writing 2 then 5."),
    case("array_element_contained_format", "13.2.2", "S13.2.2-004", "array-element-contained-format", "restriction",
         "Complete format specification within one array element",
         ["character(len=7) :: fmt(2)", "character(len=3) :: buf"], ["fmt = [character(len=7) :: '(SS,I3)', '(SS,I1)']", "buf = '###'"],
         ["write(buf,fmt(1)) 7"], [char_check("buf", "  7")], [("contained-element-format", "'(SS,I3)'", "'(SS,I2)'")],
         "Using fmt(1) alone is conforming because the whole (I3) format specification is contained in that element."),
    case("data_edit_desc_item", "13.3.1", "R1304", "data-edit-desc-item", "syntax",
         "Data edit descriptor as a format item",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I2)') 6"], [char_check("buf", " 6")],
         [("data-edit-width", "'(SS,I2)'", "'(SS,I1)'")], "R1304 includes a data-edit-desc format item; I2 writes 6 in width 2."),
    case("control_edit_desc_item", "13.3.1", "R1304", "control-edit-desc-item", "syntax",
         "Control edit descriptor as a format item",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,1X,I1)') 7"], [char_check("buf", " 7 ")],
         [("control-edit-x", "1X", "2X")], "R1304 includes a control-edit-desc; 1X advances one position before I1 writes 7."),
    case("char_string_edit_desc_item", "13.3.1", "R1304", "char-string-edit-desc-item", "syntax",
         "Character string edit descriptor as a format item",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(\"AB\")')"], [char_check("buf", "AB")],
         [("character-string-descriptor", "\"AB\"", "\"AC\"")], "R1304 includes a char-string-edit-desc, which writes the two literal characters AB."),
    case("nested_format_items_item", "13.3.1", "R1304", "nested-format-items-item", "syntax",
         "Parenthesized nested format item",
         ["character(len=4) :: buf"], ["buf = '####'"], ["write(buf,'(SS,2(I1,\",\"))') 3,4"], [char_check("buf", "3,4,")],
         [("nested-repeat-count", "2(I1", "1(I1")], "R1304 permits a repeated parenthesized format item; two copies write '3,' then '4,'."),
    case("asterisk_parenthesized_list", "13.3.1", "R1305", "asterisk-parenthesized-list", "syntax",
         "Asterisk followed by parenthesized format-items",
         ["character(len=5) :: buf"], ["buf = '#####'"], ["write(buf,'(SS,*(I1,:,\";\"))') 4,5,6"], [char_check("buf", "4;5;6")],
         [("unlimited-asterisk", "'(SS,*(I1,:,\";\"))'", "'(SS,2(I1,:,\";\"))'")],
         "R1305 syntax is * followed by a parenthesized list; p8 reuses that list for all three items on one record."),
    case("integer_literal_repeat", "13.3.1", "R1306", "integer-literal-repeat", "syntax",
         "Integer literal repeat specification",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,3I1)') 1,2,3"], [char_check("buf", "123")],
         [("integer-repeat-count", "3I1", "2I1")], "R1306 makes the integer literal 3 a repeat specification for three I1 data edit descriptors."),
    case("repeat_specification_term", "13.3.1", "R1306", "repeat-specification-term", "syntax",
         "Repeat specification term applied to a format item",
         ["character(len=4) :: buf"], ["buf = '####'"], ["write(buf,'(SS,2(I1,\"/\"))') 4,5"], [char_check("buf", "4/5/")],
         [("repeat-term-count", "2(I1", "1(I1")], "13.3.1 p1 names the literal 2 as the repeat specification applied to the parenthesized item."),
    case("unlimited_item_with_data_descriptor", "13.3.1", "C1303", "unlimited-item-with-data-descriptor", "restriction",
         "Unlimited item contains a data edit descriptor",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,*(I1))') 7,8,9"], [char_check("buf", "789")],
         [("unlimited-data-descriptor-width", "I1", "I2")], "C1303 is satisfied because the unlimited item contains data edit descriptor I1, reused for all items."),
    case("positive_repeat", "13.3.1", "C1304", "positive-repeat", "restriction",
         "Positive repeat specification",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,2I1)') 4,5"], [char_check("buf", "45")],
         [("positive-repeat-count", "2I1", "1I1")], "C1304 is satisfied because repeat r=2 is positive and produces two I1 transfers."),
    case("default_kind_repeat", "13.3.1", "C1305", "default-kind-repeat", "restriction",
         "Repeat specification without kind parameter",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,3I1)') 4,5,6"], [char_check("buf", "456")],
         [("default-kind-repeat-count", "3I1", "2I1")], "C1305 is satisfied because repeat r is the default-kind literal 3 with no kind parameter."),
    case("descriptor_and_item_drive_output", "13.4", "S13.4-001", "descriptor-and-item-drive-output", "effect",
         "Next descriptor and next item drive transfer",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I2)') 9"], [char_check("buf", " 9")],
         [("data-descriptor-width", "'(SS,I2)'", "'(SS,I1)'")], "13.4 p1 uses the next I2 descriptor with the next effective item 9 to produce a width-2 field."),
    case("descriptor_without_item_control", "13.4", "S13.4-001", "descriptor-without-item-control", "effect",
         "Descriptor without list item communicates with record",
         ["character(len=1) :: buf"], ["buf = '#'"], ["write(buf,'(\"A\")')"], [char_check("buf", "A")],
         [("character-control-output", "\"A\"", "\"B\"")], "13.4 p1 permits a descriptor action with no effective item; the string descriptor writes A."),
    case("item_list_with_data_descriptor", "13.4", "S13.4-002", "item-list-with-data-descriptor", "restriction",
         "Nonempty list with a data edit descriptor",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,\"A\",I1)') 7"], [char_check("buf", "A7")],
         [("required-data-descriptor", "I1", "I2")], "13.4 p2 is satisfied because the nonempty list has data descriptor I1 after the literal A."),
    case("left_to_right_order", "13.4", "S13.4-003", "left-to-right-order", "effect",
         "Format items interpreted left to right",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,\"A\",I1,\"B\")') 7"], [char_check("buf", "A7B")],
         [("left-to-right-sequence", "write(buf,'(SS,\"A\",I1,\"B\")') 7", "write(buf,'(SS,\"B\",I1,\"A\")') 7")],
         "13.4 p3 interprets the literal A, then I1 for item 7, then literal B from left to right."),
    case("repeat_exception", "13.4", "S13.4-003", "repeat-exception", "effect",
         "Repeat specifications are an exception to single left-to-right occurrence",
         ["character(len=4) :: buf"], ["buf = '####'"], ["write(buf,'(SS,2(\"Q\",I1))') 4,5"], [char_check("buf", "Q4Q5")],
         [("repeat-exception-count", "2(\"Q\",I1)", "1(\"Q\",I1)")], "13.4 p3 excepts repeat specifications, so the Q/I1 item is processed twice."),
    case("reversion_exception", "13.4", "S13.4-003", "reversion-exception", "effect",
         "Format reversion is an exception to one pass",
         ["character(len=1) :: rec(2)", "character(len=2) :: observed"], ["rec = '#'", "observed = '##'"],
         ["write(rec,'(SS,I1)') 1,2", "observed = rec(1) // rec(2)"], [char_check("observed", "12")],
         [("reversion-to-unlimited", "'(SS,I1)'", "'(SS,*(I1))'")], "13.4 p3 excepts format reversion; after I1 handles 1, complete-format reversion handles 2 on the next record."),
    case("repeated_data_descriptor", "13.4", "S13.4-004", "repeated-data-descriptor", "effect",
         "Repeat before data descriptor creates repeated items",
         ["character(len=6) :: buf"], ["buf = '######'"], ["write(buf,'(SS,3I2)') 1,2,3"], [char_check("buf", " 1 2 3")],
         [("repeated-data-count", "3I2", "2I2")], "13.4 p4 processes 3I2 as three comma-separated I2 items, one for each integer."),
    case("repeated_parenthesized_group", "13.4", "S13.4-004", "repeated-parenthesized-group", "effect",
         "Repeat before parenthesized group creates repeated groups",
         ["character(len=4) :: buf"], ["buf = '####'"], ["write(buf,'(SS,2(I1,\",\"))') 6,7"], [char_check("buf", "6,7,")],
         [("repeated-group-literal", "\",\"", "\";\"")], "13.4 p4 processes 2(I1, comma) as two copies of the group, producing 6, then 7,."),
    case("one_data_descriptor_per_item", "13.4", "S13.4-005", "one-data-descriptor-per-item", "effect",
         "One data edit descriptor corresponds to one item",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I1,I1)') 4,5"], [char_check("buf", "45")],
         [("insert-character-between-data", "'(SS,I1,I1)'", "'(SS,I1,\"X\",I1)'")], "13.4 p5 maps the two I1 data edit descriptors to the two integer effective items."),
    case("complex_item_two_real_descriptors", "13.4", "S13.4-005", "complex-item-two-real-descriptors", "effect",
         "A complex effective item consumes two real-family descriptors",
         ["character(len=10) :: buf", "complex :: z"], ["buf = '##########'", "z = cmplx(2.5, -3.5)"],
         ["write(buf,'(SS,F5.1,F5.1)') z"], [char_check("buf", "  2.5 -3.5")],
         [("complex-second-real-width", "F5.1,F5.1", "F5.1,F4.1")],
         "13.4 p5 makes one complex effective item consume two F descriptors; 2.5 and -3.5 are exactly representable, SS suppresses any optional plus, and F5.1 has no discarded digits or leading-zero latitude for magnitudes above one."),
    case("control_and_character_no_item", "13.4", "S13.4-005", "control-and-character-no-item", "effect",
         "Control and character descriptors have no corresponding item",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(\"A\",1X,\"B\")')"], [char_check("buf", "A B")],
         [("control-no-item-spacing", "1X", "2X")], "13.4 p5 gives no list item to the character descriptors or 1X control descriptor; they write A, blank, B."),
    case("data_descriptor_transfers_and_proceeds", "13.4", "S13.4-006", "data-descriptor-transfers-and-proceeds", "effect",
         "Data descriptor transmits and format control proceeds",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I1,I1)') 6,8"], [char_check("buf", "68")],
         [("first-data-width", "'(SS,I1,I1)'", "'(SS,I2,I1)'")], "13.4 p6 transmits item 6 with the first I1 and proceeds to transmit item 8 with the second I1."),
    case("data_descriptor_without_item_terminates", "13.4", "S13.4-006", "data-descriptor-without-item-terminates", "effect",
         "Data descriptor without corresponding item terminates",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I1,I1)') 4"], [char_check("buf", "4 ")],
         [("missing-second-item", "'(SS,I1,I1)'", "'(SS,I1,\"X\")'")], "13.4 p6 writes the first item with the first I1, then terminates at the second I1 because no item remains."),
    case("colon_with_following_item_continues", "13.4", "S13.4-007", "colon-with-following-item-continues", "effect",
         "Colon does not terminate when another item exists",
         ["character(len=3) :: buf"], ["buf = '###'"], ["write(buf,'(SS,I1,:,\",\",I1)') 4,5"], [char_check("buf", "4,5")],
         [("colon-with-item", "'(SS,I1,:,\",\",I1)'", "'(SS,I1,1X,\",\",I1)'")], "13.4 p7 does not terminate at colon because item 5 remains, so comma and second I1 are processed."),
    case("colon_without_following_item_terminates", "13.4", "S13.4-007", "colon-without-following-item-terminates", "effect",
         "Colon terminates when no further item exists",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I1,:,\",\",I1)') 4"], [char_check("buf", "4 ")],
         [("colon-without-item", "'(SS,I1,:,\",\",I1)'", "'(SS,I1,\",\",I1)'")], "13.4 p7 terminates at colon after item 4 because no further effective item is specified."),
    case("unlimited_item_reuses_list", "13.4", "S13.4-008", "unlimited-item-reuses-list", "effect",
         "Unlimited item reuses its enclosed list",
         ["character(len=5) :: buf"], ["buf = '#####'"], ["write(buf,'(SS,*(I1,:,\";\"))') 1,2,3"], [char_check("buf", "1;2;3")],
         [("unlimited-reuse-asterisk", "'(SS,*(I1,:,\";\"))'", "'(SS,2(I1,:,\";\"))'")], "13.4 p8 reverts at the unlimited item's right parenthesis to reuse its enclosed I1/list for all items."),
    case("unlimited_reversion_no_record_positioning", "13.4", "S13.4-008", "unlimited-reversion-no-record-positioning", "effect",
         "Unlimited reversion does not position to a new record",
         ["character(len=5) :: buf"], ["buf = '#####'"], ["write(buf,'(SS,*(I1,:,\",\"))') 4,5,6"], [char_check("buf", "4,5,6")],
         [("unlimited-vs-complete-reversion", "'(SS,*(I1,:,\",\"))'", "'(SS,2(I1,:,\",\"))'")], "13.4 p8 unlimited reversion has no slash-like positioning; all three comma-separated items stay in one scalar record."),
    case("unlimited_reversion_modes_unchanged", "13.4", "S13.4-008", "unlimited-reversion-modes-unchanged", "effect",
         "Unlimited reversion does not change sign mode",
         ["character(len=4) :: buf"], ["buf = '####'"], ["write(buf,'(SP,*(I2))') 7,8"], [char_check("buf", "+7+8")],
         [("unlimited-mode-preservation", "*(I2)", "(I2)")], "SP sets plus-sign mode; p8 says unlimited reversion itself does not change modes, so both I2 fields have plus signs."),
    case("complete_format_terminates_without_item", "13.4", "S13.4-009", "complete-format-terminates-without-item", "effect",
         "Complete format terminates when no item remains",
         ["character(len=2) :: buf"], ["buf = '##'"], ["write(buf,'(SS,I1)') 7"], [char_check("buf", "7 ")],
         [("extra-item-would-revert", "'(SS,I1)'", "'(SS,I1,\"X\")'")], "13.4 p9 terminates at the complete format right parenthesis because no further item remains."),
    case("nested_group_reversion_target", "13.4", "S13.4-009", "nested-group-reversion-target", "effect",
         "Complete reversion targets last preceding parenthesized item",
         ["character(len=3) :: rec(3)", "character(len=9) :: observed"], ["rec = '#'", "observed = '#########'"],
         ["write(rec,'(SS,\"H\",(I1,\",\"))') 1,2,3", "observed = rec(1) // rec(2) // rec(3)"], [char_check("observed", "H1,2, 3, ")],
         [("remove-nested-group-target", "'(SS,\"H\",(I1,\",\"))'", "'(SS,\"H\",I1,\",\")'")],
         "After H1, complete-format reversion targets the nested (I1, comma), so later records are '2, ' and '3, '."),
    case("no_preceding_parenthesis_fallback", "13.4", "S13.4-009", "no-preceding-parenthesis-fallback", "effect",
         "Complete reversion falls back to first left parenthesis",
         ["character(len=2) :: rec(3)", "character(len=6) :: observed"], ["rec = '#'", "observed = '######'"],
         ["write(rec,'(SS,\"H\",I1)') 1,2,3", "observed = rec(1) // rec(2) // rec(3)"], [char_check("observed", "H1H2H3")],
         [("introduce-preceding-parenthesis", "'(SS,\"H\",I1)'", "'(SS,\"H\",(I1))'")],
         "With no preceding parenthesized format item, p9 reversion returns to the first left parenthesis and re-emits H."),
    case("repeat_reused_on_reversion", "13.4", "S13.4-009", "repeat-reused-on-reversion", "effect",
         "Repeat before reversion target is reused",
         ["character(len=3) :: rec(3)", "character(len=9) :: observed"], ["rec = '#'", "observed = '#########'"],
         ["write(rec,'(SS,\"H\",2(I1))') 1,2,3,4,5,6", "observed = rec(1) // rec(2) // rec(3)"], [char_check("observed", "H1234 56 ")],
         [("reversion-repeat-count", "2(I1)", "1(I1)")], "P9 reuses the repeat 2 before the reversion target, so later records contain two I1 fields each."),
    case("complete_reversion_modes_unchanged", "13.4", "S13.4-009", "complete-reversion-modes-unchanged", "effect",
         "Complete reversion itself does not change sign mode",
         ["character(len=2) :: rec(2)", "character(len=4) :: observed"], ["rec = '#'", "observed = '####'"],
         ["write(rec,'(SP,(I2))') 7,8", "observed = rec(1) // rec(2)"], [char_check("observed", "+7+8")],
         [("complete-mode-sign", "SP", "SS")], "SP is processed before the nested I2; p9 reversion to (I2) does not reset the sign mode, so + appears again."),
    case("reversion_positions_like_slash", "13.4", "S13.4-009", "reversion-positions-like-slash", "effect",
         "Complete reversion positions like slash processing",
         ["character(len=1) :: rec(3)", "character(len=3) :: observed"], ["rec = '#'", "observed = '###'"],
         ["write(rec,'(SS,I1)') 1,2,3", "observed = rec(1) // rec(2) // rec(3)"], [char_check("observed", "123")],
         [("complete-vs-unlimited-positioning", "'(SS,I1)'", "'(SS,*(I1))'")], "P9 positions the internal file as slash processing would on each complete-format reversion, filling three records."),
    case("reused_portion_with_data_descriptor", "13.4", "S13.4-010", "reused-portion-with-data-descriptor", "restriction",
         "Reused portion contains a data edit descriptor",
         ["character(len=2) :: rec(2)", "character(len=4) :: observed"], ["rec = '#'", "observed = '####'"],
         ["write(rec,'(SS,\"X\",(I1))') 1,2", "observed = rec(1) // rec(2)"], [char_check("observed", "X12 ")],
         [("reused-data-width", "(I1)", "(I2)")], "The p9 reused portion is the nested (I1), which contains a data edit descriptor as required by S13.4-010."),
]

VARIANTS = {row["variant"]: row for row in CASES}
FACETS_BY_RULE = {}
for row in CASES:
    FACETS_BY_RULE.setdefault(row["rule"], []).extend(row["facets"])
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in sorted(FACETS_BY_RULE.items())}
SELECTED_BY_RULE = {rule: set(facets) for rule, facets in FACETS_BY_RULE.items()}
ORACLE_PREFIX = {rule: f"{rule} format_13_2_13_4 fixture observations: " for rule in FACETS_BY_RULE}
LIMIT_PREFIX = {rule: f"{rule} format_13_2_13_4 fixture boundaries: " for rule in FACETS_BY_RULE}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    row = VARIANTS[variant]
    return row["rule"].replace(".", "_").replace("-", "_") + "_valid__format_13_2_13_4_" + variant


def fortran_char_literal(value):
    return "'" + value.replace("'", "''") + "'"


def altered_char(value):
    chars = list(value)
    for i, ch in enumerate(chars):
        if ch == " ":
            chars[i] = "#"
            return "".join(chars)
    if chars:
        chars[-1] = "Z" if chars[-1] != "Z" else "Y"
        return "".join(chars)
    return "X"


class Program:
    def __init__(self, spec):
        self.spec = spec
        self.text = ""
        self.guards = []
        self.observations = []
        self.probes = []
        self.feature_mutations = []
        self.omissions = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def token(self, name):
        return f"F132134:{self.spec['variant']}:{name}"

    def guard_equal(self, name, expression, expected, replacement, category="oracle", count=True):
        block_start = len(self.text)
        prefix = f"  if ({expression} /= {expected}) then\n"
        start = block_start + prefix.index(expected)
        token = self.token(name)
        self.add(prefix)
        self.add(f"    write(*,'(a)') '{token}'\n    error stop 1\n  end if\n")
        if count:
            self.add("  checks = checks + 1\n")
        mutation = dict(id=name, kind="guard", category=category, mutation="guard-expectation",
                        expected=expected, replacement=replacement, span=[start, start + len(expected)],
                        line=self.text[:start].count("\n") + 1, failure_stdout=token + "\n",
                        block_span=[block_start, len(self.text)])
        self.guards.append(mutation)
        self.probes.append(dict(mutation))
        if count:
            self.observations.append(mutation)
        return mutation

    def char_observation(self, check):
        expected = check["expected"]
        label = check["label"]
        self.guard_equal(label + "-length", f"len({check['expr']})", str(len(expected)), str(len(expected) + 1), "length")
        self.guard_equal(label + "-characters", check["expr"], fortran_char_literal(expected),
                         fortran_char_literal(altered_char(expected)), "oracle")

    def finish(self):
        total = len(self.observations)
        self.guard_equal("check-total", "checks", str(total), str(total + 1), "completion", count=False)
        literal = completion(self.spec)
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        block = self.add(prefix + literal + "'\n")
        self.probes.append(dict(id="completion-output", kind="output", category="completion",
                                mutation="completion-literal", expected=literal,
                                replacement=literal.replace(" OK", " BAD"),
                                span=[start, start + len(literal)], line=self.text[:start].count("\n") + 1,
                                failure_stdout="", block_span=block))
        self.add(f"end program f132134_{self.spec['variant']}\n")
        self.omissions.append(dict(id="omit-completion", kind="output", category="omission",
                                   mutation="completion-statement-omission", span=block,
                                   expected=self.text[block[0]:block[1]], replacement="",
                                   line=self.text[:block[0]].count("\n") + 1, failure_stdout=""))
        for action_span, action_text in self.action_spans:
            if not action_text.lstrip().lower().startswith("write"):
                continue
            self.omissions.append(dict(id="omit-action-" + str(len(self.omissions)), kind="feature",
                                       category="feature-omission", mutation="action-omission",
                                       span=action_span, expected=action_text, replacement="",
                                       line=self.text[:action_span[0]].count("\n") + 1, failure_stdout=""))


def completion(spec):
    return "FORMAT 13.2-13.4 " + spec["variant"].upper() + " OK"


def emit_program(spec):
    p = Program(spec)
    p.action_spans = []
    p.add(f"! rule: {spec['rule']}\n")
    for facet in spec["facets"]:
        p.add(f"! covers: {facet}\n")
    p.add("! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.\n")
    p.add(f"program f132134_{spec['variant']}\n")
    p.add("  implicit none\n")
    p.add("  integer :: checks\n")
    for decl in spec["declarations"]:
        p.add("  " + decl + "\n")
    p.add("  checks = 0\n")
    for line in spec["setup"]:
        p.add("  " + line + "\n")
    for line in spec["actions"]:
        span = p.add(("" if line and line[0].isdigit() else "  ") + line + "\n")
        p.action_spans.append((span, p.text[span[0]:span[1]]))
    for check in spec["checks"]:
        if check["kind"] != "char":
            raise ValueError("unsupported check kind")
        p.char_observation(check)
    for mut_id, expected, replacement in spec["features"]:
        occurrences = [i for i in range(len(p.text)) if p.text.startswith(expected, i)]
        if len(occurrences) != 1:
            raise ValueError(f"{spec['variant']} feature {mut_id} has {len(occurrences)} occurrences of {expected!r}")
        start = occurrences[0]
        p.feature_mutations.append(dict(id=mut_id, kind="feature", category="feature-substitution",
                                        mutation="feature-substitution", expected=expected,
                                        replacement=replacement, span=[start, start + len(expected)],
                                        line=p.text[:start].count("\n") + 1, failure_stdout=""))
    p.finish()
    return finalize(p, spec)


def finalize(p, spec):
    raw = p.text.encode("ascii")
    for mutation in p.probes + p.feature_mutations + p.omissions:
        start, end = mutation["span"]
        if raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError(f"{spec['variant']} mutation {mutation['id']} lost complete parent binding")
    return dict(id=identifier(spec["variant"]), variant=spec["variant"], rule=spec["rule"], facets=spec["facets"],
                evidence=spec["evidence"], standard="f2023", phase="run", title=spec["title"],
                source=p.text, source_sha256=sha(raw), completion=completion(spec) + "\n",
                expected=[check["expected"] for check in spec["checks"]], derivation=spec["derivation"],
                guards=p.guards, observations=p.observations, probes=p.probes,
                feature_mutations=p.feature_mutations, omissions=p.omissions,
                mutations=p.feature_mutations + p.probes + p.omissions,
                expected_counts=dict(checks=len(p.observations)))


def source_specs():
    return {identifier(row["variant"]): emit_program(row) for row in CASES}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent source no longer matches fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span no longer binds complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def rule_oracle(rule):
    cases = [row for row in CASES if row["rule"] == rule]
    return ORACLE_PREFIX[rule] + " ".join(
        f"{row['variant']} covers {row['facets'][0]}: {row['derivation']}" for row in cases)


def rule_limitation(rule):
    pending_note = (
        "Only the listed executable positive/effect facets are removed from pending. Invalid FORMAT statements, "
        "invalid character format strings detectable only during data transfer, undefined/stability negatives, DT "
        "defined-I/O reversion, complex real-family descriptor consumption, and processor-dependent or message-text "
        "diagnostics remain pending. All positive numeric output uses I/A/character descriptors, or SP where a plus "
        "sign is required by the sign mode; no leading-zero, real rounding, IOSTAT value, or IOMSG text is asserted. "
        "Every internal output buffer or record is prefilled with '#', every character assertion checks LEN before "
        "equality, and each case has permanent feature-substitution and action-omission mutants."
    )
    return LIMIT_PREFIX[rule] + pending_note


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, selected in SELECTED_BY_RULE.items():
        if rule not in by_rule:
            continue
        req = by_rule[rule]
        if not selected <= set(req["facets"]):
            raise ValueError("selected facets are not declared for " + rule)
        for facet in selected:
            req.get("pending", {}).pop(facet, None)
        req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIX[rule], rule_oracle(rule))
        req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIX[rule], rule_limitation(rule))
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    selected = [row for row in CASES if row["section"] == section]
    if selected:
        facets = sorted({facet for row in selected for facet in row["facets"]})
        summary = (SUMMARY_BEGIN + "\n"
                   f"## FORMAT / character-format / format-control runtime observations for {section}\n\n"
                   f"This packet contributes {len(selected)} run/f2023 fixture(s) covering {len(facets)} selected facet(s). "
                   "The oracles use internal formatted output with I, A, character-string, colon, repeat, and reversion "
                   "effects only; buffers are sentinel-filled, LEN is checked before character equality, and permanent "
                   "feature mutations are generated for mutation checking on both toolchains. Remaining negative or "
                   "processor-latitude plans stay pending.\n" + SUMMARY_END)
        if SUMMARY_BEGIN in before or SUMMARY_END in before:
            leading, owned = before.split(SUMMARY_BEGIN)
            _, trailing = owned.split(SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        updated = synced_catalogue(catalogue)
        updated_catalogues[section] = updated
        updated_views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, rel in CATALOGUES.items():
            if json.loads((root / rel).read_text()) != updated_catalogues[section]:
                stale.append(rel)
            if (root / VIEWS[section]).read_text() != updated_views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale format_13_2_13_4 fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for section, rel in CATALOGUES.items():
                (root / rel).write_text(json.dumps(updated_catalogues[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(updated_views[section])
    return specs


def compiler_command(compiler, std, source, output):
    compiler = Path(compiler)
    flag = "--std=" if "lfortran" in compiler.name.lower() else "-std="
    command = [str(compiler)]
    if std:
        command.append(flag + std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    case_dir = work_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    compile_run = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
    if compile_run.returncode != 0:
        return dict(status="compile-fail", stdout=compile_run.stdout, stderr=compile_run.stderr,
                    returncode=compile_run.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
    passed = (run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "")
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    specs = source_specs()
    work_dir = root / ".format_13_2_13_4_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"], spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            for index, mutation in enumerate(spec["mutations"]):
                mutant = spec["source"] if inject_survivor and not report else mutated_source(spec, mutation).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant, spec["completion"], f"{spec['variant']}_mut_{index:03d}")
                failed = observed["status"] != "pass"
                report.append(dict(variant=spec["variant"], mutation_id=mutation["id"], mutation=mutation["mutation"],
                                   category=mutation["category"], expected=mutation["expected"], replacement=mutation["replacement"],
                                   parent_ok=parent_ok, failed=failed, status=observed["status"], stdout=observed["stdout"],
                                   stderr=observed["stderr"], returncode=observed["returncode"]))
        bad = [row for row in report if not row["parent_ok"] or row["status"] == "compile-fail" or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def counts(specs):
    return dict(cases=len(specs), facets=len({facet for spec in specs.values() for facet in spec["facets"]}),
                mutations=sum(len(spec["mutations"]) for spec in specs.values()),
                feature=sum(len(spec["feature_mutations"]) for spec in specs.values()),
                omissions=sum(len(spec["omissions"]) for spec in specs.values()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    selected = [args.check, args.sync_catalogues, args.mutation_check]
    if sum(bool(x) for x in selected) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work, args.inject_surviving_mutant)
        feature = sum(row["category"].startswith("feature") for row in report)
        print(f"Mutation-checked {len(report)} format_13_2_13_4 mutants on {args.compiler}: {feature} feature/action mutants; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    c = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {c['cases']} format_13_2_13_4 cases, {c['facets']} facets, "
          f"{c['mutations']} mutations ({c['feature']} feature substitutions, {c['omissions']} omissions).")


if __name__ == "__main__":
    main()
