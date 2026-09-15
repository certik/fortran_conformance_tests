! rule: S7.4.4.1-002
! covers: named-method-selection
! evidence: effect
! standard: f2023
program character_type_case
use iso_fortran_env, only: character_kinds
implicit none
integer :: ascii, ucs
if (selected_char_kind('DEFAULT') /= kind('A')) error stop 1
if (selected_char_kind('dEfAuLt   ') /= kind('A')) error stop 2
if (.not. any(character_kinds == kind('A'))) error stop 3
ascii = selected_char_kind('ASCII')
ucs = selected_char_kind('ISO_10646')
if (ascii < -1 .or. ucs < -1) error stop 4
if (selected_char_kind('aScIi   ') /= ascii) error stop 5
if (selected_char_kind('iSo_10646   ') /= ucs) error stop 6
if (ascii >= 0) then
    if (.not. any(character_kinds == ascii)) error stop 7
end if
if (ucs >= 0) then
    if (.not. any(character_kinds == ucs)) error stop 8
end if
end program
