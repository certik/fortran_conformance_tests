! rule: S7.4.4.4-002
! covers: blank-digit-uppercase-alternatives
! evidence: effect
! standard: f2023
program character_type_case
implicit none
logical :: digits_first, letters_first
digits_first = ' ' < '0' .and. '0' < '9' .and. '9' < 'A'
letters_first = ' ' < 'A' .and. 'A' < 'Z' .and. 'Z' < '0'
if (.not. (digits_first .or. letters_first)) error stop 1
end program
