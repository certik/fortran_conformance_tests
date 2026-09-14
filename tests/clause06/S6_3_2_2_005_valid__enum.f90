! rule: S6.3.2.2-005
! covers: end-enum
! evidence: positive-control
program enum_spellings
  implicit none
  enum, bind(c)
    enumerator :: first = 1
  endenum
  enum, bind(c)
    enumerator :: second = 2
  end enum
  if (first /= 1) stop 1
  if (second /= 2) stop 2
end program
