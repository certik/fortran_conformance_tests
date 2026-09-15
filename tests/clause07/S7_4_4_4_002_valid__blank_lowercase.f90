! rule: S7.4.4.4-002
! covers: blank-digit-lowercase-alternatives
! evidence: effect
! standard: f2023
program character_type_case
implicit none
logical :: digits_first, letters_first
digits_first = ' ' < '0' .and. '0' < '9' .and. '9' < 'a'
letters_first = ' ' < 'a' .and. 'a' < 'z' .and. 'z' < '0'
if (.not. (digits_first .or. letters_first)) error stop 1
end program
