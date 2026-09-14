! rule: S6.3.2.5-002
! covers: same-line-successor continued-successor terminator-elision separator-sequence
! evidence: effect
program semicolon_separators
  implicit none
  integer :: a, b, c
  a = -1
  b = -1
  c = -1
  a = 3; b = a + 4
  if (a /= 3) error stop 1
  if (b /= 7) error stop 2
  a = 5; ;;;  ; b = a + 6;  ;;
  if (a /= 5) error stop 3
  if (b /= 11) error stop 4
  a = 7; c = a + &
    & 2; b = c + 1
  if (a /= 7) error stop 5
  if (c /= 9) error stop 6
  if (b /= 10) error stop 7
end program
