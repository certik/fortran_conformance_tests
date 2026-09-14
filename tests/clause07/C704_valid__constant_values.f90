! rule: C704
! covers: constant-values
! evidence: positive-control
program c704_constants
    implicit none
    integer, parameter :: ik = kind(0), ck = kind('a'), n = 3
    integer(ik) :: code
    character(kind=ck, len=n) :: text
    code = 7
    text = 'abc'
    if (kind(code) /= ik .or. kind(text) /= ck) error stop 'kinds'
    if (len(text) /= 3) error stop 'length'
    if (code /= 7 .or. text /= 'abc') error stop 'values'
end program
