! rule: S6.3.2.2-003
! covers: keyword-character-constant
! evidence: effect
program separator_character
  implicit none
  print'(A)', 'X' ! {error S6.3.2.2-003}
end program
