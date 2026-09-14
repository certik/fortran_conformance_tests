! rule: S6.3.2.2-005
! covers: double-precision
! evidence: positive-control
program double_precision_spellings
  implicit none
  doubleprecision :: compact
  double precision :: spaced
  double   precision :: multiple
  compact = 4.0d0
  spaced = 5.0d0
  multiple = 6.0d0
  if (compact /= 4.0d0) stop 1
  if (spaced /= 5.0d0) stop 2
  if (multiple /= 6.0d0) stop 3
end program
