! rule: S6.3.2.2-003
! covers: keyword-integer-constant
! evidence: effect
program separator_integer
  implicit none
  stop0 ! {error S6.3.2.2-003}
end program
